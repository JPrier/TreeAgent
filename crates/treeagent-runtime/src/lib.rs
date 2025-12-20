use treeagent_model::GraphSpec;

#[derive(Debug, Default, Clone)]
pub struct WorkspaceRuntime {
    graph_spec: GraphSpec,
}

impl WorkspaceRuntime {
    pub fn new(name: impl Into<String>) -> Self {
        Self {
            graph_spec: GraphSpec::new(name),
        }
    }

    pub fn summary(&self) -> String {
        format!(
            "TreeAgent runtime initialized for graph '{}'",
            self.graph_spec.name()
        )
    }

    pub fn print_summary(&self) -> anyhow::Result<()> {
        println!("{}", self.summary());
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn summary_mentions_runtime() {
        let runtime = WorkspaceRuntime::new("demo");
        let summary = runtime.summary();
        assert!(summary.contains("TreeAgent runtime initialized for graph 'demo'"));
    }
}
