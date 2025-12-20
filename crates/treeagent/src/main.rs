use treeagent_runtime::WorkspaceRuntime;

fn main() {
    let runtime = WorkspaceRuntime::default();
    runtime
        .print_summary()
        .expect("failed to start the TreeAgent runtime");
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn runtime_runs() {
        let runtime = WorkspaceRuntime::default();
        let summary = runtime.summary();
        assert!(summary.contains("TreeAgent runtime"));
    }
}
