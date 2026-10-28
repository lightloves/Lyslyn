use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use std::fs;
use std::path::Path;

#[derive(Debug, Serialize, Deserialize)]
pub struct PackageMeta {
    pub name: String,
    pub version: String,
    pub description: Option<String>,
    pub authors: Option<Vec<String>>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Manifest {
    pub package: PackageMeta,
    #[serde(default)]
    pub dependencies: BTreeMap<String, String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Lockfile {
    pub version: u32,
    pub packages: BTreeMap<String, String>,
}

impl Manifest {
    pub fn new(name: &str) -> Self {
        Manifest {
            package: PackageMeta {
                name: name.to_string(),
                version: "0.1.0".to_string(),
                description: Some("A Lyslyn project".to_string()),
                authors: Some(vec!["Developer".to_string()]),
            },
            dependencies: BTreeMap::new(),
        }
    }

    pub fn load_from_dir(dir: &Path) -> Result<Self, String> {
        let manifest_path = dir.join("lyslyn.toml");
        if !manifest_path.exists() {
            return Err("lyslyn.toml not found in current directory".to_string());
        }
        let content = fs::read_to_string(&manifest_path)
            .map_err(|e| format!("Failed to read lyslyn.toml: {}", e))?;
        toml::from_str(&content).map_err(|e| format!("Failed to parse lyslyn.toml: {}", e))
    }

    pub fn save_to_dir(&self, dir: &Path) -> Result<(), String> {
        let manifest_path = dir.join("lyslyn.toml");
        let content = toml::to_string_pretty(self)
            .map_err(|e| format!("Failed to serialize manifest: {}", e))?;
        fs::write(&manifest_path, content)
            .map_err(|e| format!("Failed to write lyslyn.toml: {}", e))
    }
}
