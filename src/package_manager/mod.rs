pub mod manifest;

pub use manifest::{Lockfile, Manifest, PackageMeta};
use std::fs;
use std::path::Path;

pub fn init_project(name: &str) -> Result<(), String> {
    let cwd = Path::new(".");
    let manifest_path = cwd.join("lyslyn.toml");
    if manifest_path.exists() {
        return Err("lyslyn.toml already exists in current directory".to_string());
    }

    let manifest = Manifest::new(name);
    manifest.save_to_dir(cwd)?;

    let src_dir = cwd.join("src");
    if !src_dir.exists() {
        fs::create_dir_all(&src_dir).map_err(|e| e.to_string())?;
        let main_file = src_dir.join("main.lys");
        let initial_code = format!(
            "Say \"Hello from {}!\"\nSet version to \"0.1.0\"\nSay \"Version:\", version\n",
            name
        );
        fs::write(main_file, initial_code).map_err(|e| e.to_string())?;
    }

    println!("✓ Initialized new Lyslyn project '{}' (lyslyn.toml, src/main.lys)", name);
    Ok(())
}

pub fn install_package(pkg: &str) -> Result<(), String> {
    let cwd = Path::new(".");
    let mut manifest = Manifest::load_from_dir(cwd)?;

    manifest.dependencies.insert(pkg.to_string(), "*".to_string());
    manifest.save_to_dir(cwd)?;

    println!("✓ Added package '{}' to dependencies in lyslyn.toml", pkg);
    Ok(())
}

pub fn remove_package(pkg: &str) -> Result<(), String> {
    let cwd = Path::new(".");
    let mut manifest = Manifest::load_from_dir(cwd)?;

    if manifest.dependencies.remove(pkg).is_some() {
        manifest.save_to_dir(cwd)?;
        println!("✓ Removed package '{}' from lyslyn.toml", pkg);
    } else {
        println!("Package '{}' was not found in lyslyn.toml dependencies", pkg);
    }
    Ok(())
}
