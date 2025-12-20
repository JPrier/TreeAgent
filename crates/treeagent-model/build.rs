use std::collections::BTreeSet;
use std::env;

fn main() -> anyhow::Result<()> {
    let target = env::var("TARGET").unwrap_or_else(|_| "unknown-target".to_string());
    println!("cargo:rustc-env=TREEAGENT_BUILD_TARGET={target}");

    let profile = env::var("PROFILE").unwrap_or_else(|_| "unknown-profile".to_string());
    println!("cargo:rustc-env=TREEAGENT_BUILD_PROFILE={profile}");

    let mut features = BTreeSet::new();
    for (key, _) in env::vars() {
        if let Some(feature) = key.strip_prefix("CARGO_FEATURE_") {
            features.insert(feature.to_ascii_lowercase().replace('_', "-"));
        }
    }
    let feature_list = features.into_iter().collect::<Vec<_>>().join(",");
    println!("cargo:rustc-env=TREEAGENT_BUILD_FEATURES={feature_list}");
    Ok(())
}
