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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn stores_name() {
        let spec = GraphSpec::new("example");
        assert_eq!(spec.name(), "example");
    }
}
