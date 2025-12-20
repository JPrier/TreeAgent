use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::path::{Path, PathBuf};

use anyhow::{bail, Context, Result};
use serde::{Deserialize, Serialize};

#[derive(Debug, Default, Clone, PartialEq, Eq)]
pub struct GraphSpec {
    name: String,
}

impl GraphSpec {
    pub fn new(name: impl Into<String>) -> Self {
        Self { name: name.into() }
    }

    pub fn name(&self) -> &str {
        &self.name
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct GraphIR {
    #[serde(default)]
    pub spawn_rules: BTreeMap<String, SpawnRule>,
    #[serde(default)]
    pub execution: ExecutionLimits,
    #[serde(default)]
    pub checkpoint: CheckpointMetadata,
}

impl GraphIR {
    pub fn canonicalized(mut self) -> Self {
        self.spawn_rules = self
            .spawn_rules
            .into_iter()
            .map(|(task, rule)| (task, rule.canonicalized()))
            .collect();
        self.execution = self.execution.canonicalized();
        self.checkpoint = self.checkpoint.canonicalized();
        self
    }

    pub fn validate(&self) -> Result<()> {
        for (parent, rule) in &self.spawn_rules {
            if parent.trim().is_empty() {
                bail!("spawn rule names cannot be empty");
            }
            rule.validate(parent)?;
        }
        self.execution.validate()?;
        self.checkpoint.validate()?;
        Ok(())
    }

    pub fn canonical_json(&self) -> Result<Vec<u8>> {
        let canonical = self.clone().canonicalized();
        serde_json::to_vec(&canonical).context("failed to serialize canonical graph IR")
    }

    pub fn blake3_hash(&self, manifest: &BuildManifest) -> Result<blake3::Hash> {
        let mut hasher = blake3::Hasher::new();
        hasher.update(&self.canonical_json()?);
        hasher.update(&manifest.canonical_bytes()?);
        Ok(hasher.finalize())
    }

    pub fn blake3_hex(&self, manifest: &BuildManifest) -> Result<String> {
        Ok(self.blake3_hash(manifest)?.to_hex().to_string())
    }

    pub fn load_spawn_rules_from_disk() -> Result<Self> {
        let cwd = std::env::current_dir().context("failed to resolve current directory")?;
        let path = Self::resolve_spawn_rules_path(&cwd);
        let spawn_rules = match path {
            Some(path) => {
                let data = fs::read_to_string(&path)
                    .with_context(|| format!("failed to read spawn rules at {}", path.display()))?;
                let parsed: BTreeMap<String, SpawnRule> = serde_json::from_str(&data)
                    .with_context(|| {
                        format!("failed to parse spawn rules from {}", path.display())
                    })?;
                parsed
            }
            None => BTreeMap::new(),
        };

        let ir = GraphIR {
            spawn_rules,
            ..GraphIR::default()
        }
        .canonicalized();

        ir.validate().context("invalid spawn rule configuration")?;
        Ok(ir)
    }

    fn resolve_spawn_rules_path(base: &Path) -> Option<PathBuf> {
        let primary = base.join("spawn_rules.json");
        if primary.exists() {
            return Some(primary);
        }
        let fallback = base.join("config").join("spawn_rules.json");
        if fallback.exists() {
            return Some(fallback);
        }
        None
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SpawnRule {
    #[serde(default)]
    pub can_spawn: BTreeMap<String, u32>,
    #[serde(default = "default_self_spawn")]
    pub self_spawn: bool,
    #[serde(default)]
    pub max_children: Option<u32>,
}

impl Default for SpawnRule {
    fn default() -> Self {
        Self {
            can_spawn: BTreeMap::new(),
            self_spawn: default_self_spawn(),
            max_children: None,
        }
    }
}

impl SpawnRule {
    fn canonicalized(mut self) -> Self {
        self.can_spawn = self.can_spawn.into_iter().collect();
        if let Some(0) = self.max_children {
            self.max_children = None;
        }
        self
    }

    fn validate(&self, parent: &str) -> Result<()> {
        for (child, limit) in &self.can_spawn {
            if child.trim().is_empty() {
                bail!("spawn rule '{}' has an empty child task name", parent);
            }
            if *limit == 0 {
                bail!(
                    "spawn rule '{}' cannot allow zero spawns for '{}'",
                    parent,
                    child
                );
            }
        }
        if let Some(limit) = self.max_children {
            if limit == 0 {
                bail!("spawn rule '{}' has a zero max_children limit", parent);
            }
            let total: u32 = self.can_spawn.values().copied().sum();
            if total > 0 && limit < total {
                bail!(
                    "spawn rule '{}' max_children ({}) is less than the sum of child limits ({})",
                    parent,
                    limit,
                    total
                );
            }
        }
        Ok(())
    }
}

fn default_self_spawn() -> bool {
    true
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct ExecutionLimits {
    #[serde(default)]
    pub max_depth: Option<u32>,
    #[serde(default)]
    pub max_nodes: Option<u32>,
    #[serde(default)]
    pub max_children_per_node: Option<u32>,
}

impl ExecutionLimits {
    fn canonicalized(mut self) -> Self {
        if let Some(0) = self.max_depth {
            self.max_depth = None;
        }
        if let Some(0) = self.max_nodes {
            self.max_nodes = None;
        }
        if let Some(0) = self.max_children_per_node {
            self.max_children_per_node = None;
        }
        self
    }

    fn validate(&self) -> Result<()> {
        if let Some(depth) = self.max_depth {
            if depth == 0 {
                bail!("execution limit max_depth cannot be zero");
            }
        }
        if let Some(nodes) = self.max_nodes {
            if nodes == 0 {
                bail!("execution limit max_nodes cannot be zero");
            }
        }
        if let Some(children) = self.max_children_per_node {
            if children == 0 {
                bail!("execution limit max_children_per_node cannot be zero");
            }
        }
        Ok(())
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct CheckpointMetadata {
    #[serde(default)]
    pub enabled: bool,
    #[serde(default)]
    pub interval: Option<u32>,
    #[serde(default)]
    pub tags: BTreeMap<String, String>,
}

impl CheckpointMetadata {
    fn canonicalized(mut self) -> Self {
        self.tags = self.tags.into_iter().collect();
        if let Some(0) = self.interval {
            self.interval = None;
        }
        self
    }

    fn validate(&self) -> Result<()> {
        if let Some(interval) = self.interval {
            if interval == 0 {
                bail!("checkpoint interval cannot be zero");
            }
        }
        Ok(())
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct BuildManifest {
    pub runtime_version: String,
    pub target_triple: String,
    pub profile: String,
    pub features: BTreeSet<String>,
}

impl BuildManifest {
    pub fn from_env() -> Self {
        let runtime_version = option_env!("TREEAGENT_RUNTIME_VERSION")
            .unwrap_or(env!("CARGO_PKG_VERSION"))
            .to_string();
        let target_triple = option_env!("TREEAGENT_BUILD_TARGET")
            .unwrap_or("unknown-target")
            .to_string();
        let profile = option_env!("TREEAGENT_BUILD_PROFILE")
            .unwrap_or("unknown-profile")
            .to_string();
        let features = option_env!("TREEAGENT_BUILD_FEATURES")
            .unwrap_or_default()
            .split(',')
            .filter(|s| !s.is_empty())
            .map(|s| s.to_string())
            .collect();
        Self {
            runtime_version,
            target_triple,
            profile,
            features,
        }
    }

    fn canonicalized(mut self) -> Self {
        self.features = self.features.into_iter().collect();
        self
    }

    fn canonical_bytes(&self) -> Result<Vec<u8>> {
        let canonical = self.clone().canonicalized();
        serde_json::to_vec(&canonical).context("failed to serialize build manifest")
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    #[test]
    fn stores_name() {
        let spec = GraphSpec::new("example");
        assert_eq!(spec.name(), "example");
    }

    #[test]
    fn canonicalization_sets_defaults() {
        let ir = GraphIR {
            spawn_rules: BTreeMap::from([(
                "HLD".into(),
                SpawnRule {
                    can_spawn: BTreeMap::from([("LLD".into(), 2)]),
                    self_spawn: false,
                    max_children: Some(0),
                },
            )]),
            execution: ExecutionLimits {
                max_depth: Some(0),
                ..ExecutionLimits::default()
            },
            checkpoint: CheckpointMetadata {
                interval: Some(0),
                tags: BTreeMap::from([("a".into(), "1".into()), ("b".into(), "2".into())]),
                ..CheckpointMetadata::default()
            },
        }
        .canonicalized();

        assert!(ir.spawn_rules["HLD"].max_children.is_none());
        assert!(ir.execution.max_depth.is_none());
        assert!(ir.checkpoint.interval.is_none());
        let tag_keys: Vec<_> = ir.checkpoint.tags.keys().cloned().collect();
        assert_eq!(tag_keys, vec!["a".to_string(), "b".to_string()]);
    }

    #[test]
    fn loader_prefers_cwd_rules() {
        let tmp = TempDir::new().unwrap();
        let cwd = tmp.path();

        fs::create_dir_all(cwd.join("config")).unwrap();
        fs::write(
            cwd.join("config").join("spawn_rules.json"),
            r#"{ "HLD": { "can_spawn": { "LLD": 1 } } }"#,
        )
        .unwrap();
        fs::write(
            cwd.join("spawn_rules.json"),
            r#"{ "HLD": { "can_spawn": { "TEST": 2 }, "self_spawn": false } }"#,
        )
        .unwrap();

        let original_dir = std::env::current_dir().unwrap();
        std::env::set_current_dir(cwd).unwrap();
        let loaded = GraphIR::load_spawn_rules_from_disk().unwrap();
        std::env::set_current_dir(original_dir).unwrap();

        let hld = loaded.spawn_rules.get("HLD").unwrap();
        assert_eq!(
            hld.can_spawn.keys().cloned().collect::<Vec<_>>(),
            vec!["TEST"]
        );
        assert!(!hld.self_spawn);
    }

    #[test]
    fn loader_surfaces_validation_errors() {
        let tmp = TempDir::new().unwrap();
        let cwd = tmp.path();

        fs::write(
            cwd.join("spawn_rules.json"),
            r#"{ "HLD": { "can_spawn": { "LLD": 0 } } }"#,
        )
        .unwrap();

        let original_dir = std::env::current_dir().unwrap();
        std::env::set_current_dir(cwd).unwrap();
        let result = GraphIR::load_spawn_rules_from_disk();
        std::env::set_current_dir(original_dir).unwrap();

        assert!(result.is_err());
    }

    #[test]
    fn manifest_changes_hash() {
        let ir = GraphIR {
            spawn_rules: BTreeMap::from([(
                "HLD".into(),
                SpawnRule {
                    can_spawn: BTreeMap::from([("LLD".into(), 1)]),
                    ..SpawnRule::default()
                },
            )]),
            ..GraphIR::default()
        };

        let manifest_a = BuildManifest {
            runtime_version: "0.1.0".into(),
            target_triple: "x86_64-unknown-linux-gnu".into(),
            profile: "debug".into(),
            features: BTreeSet::from(["foo".into()]),
        };
        let manifest_b = BuildManifest {
            runtime_version: "0.1.0".into(),
            target_triple: "x86_64-unknown-linux-gnu".into(),
            profile: "release".into(),
            features: BTreeSet::new(),
        };

        let hash_a = ir.blake3_hex(&manifest_a).unwrap();
        let hash_b = ir.blake3_hex(&manifest_b).unwrap();
        assert_ne!(hash_a, hash_b);
    }
}
