use treeagent_model::GraphSpec;

fn main() {
    let spec = GraphSpec::new("client");
    println!("treeagentc targeting graph: {}", spec.name());
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn client_initializes_graph_spec() {
        let spec = GraphSpec::new("client-spec");
        assert_eq!(spec.name(), "client-spec");
    }
}
