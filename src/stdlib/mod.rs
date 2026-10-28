pub mod cache;
pub mod collections;
pub mod crypto;
pub mod db;
pub mod env;
pub mod fs;
pub mod http;
pub mod json;
pub mod jwt;
pub mod log;
pub mod math;
pub mod os;
pub mod random;
pub mod regex;
pub mod server;
pub mod text;
pub mod time;
pub mod validation;

use crate::values::Value;
use indexmap::IndexMap;

pub fn get_standard_modules() -> IndexMap<String, Value> {
    let mut mods = IndexMap::new();

    mods.insert("math".to_string(), math::create_math_module());
    mods.insert("json".to_string(), json::create_json_module());
    let fs_mod = fs::create_fs_module();
    mods.insert("files".to_string(), fs_mod.clone());
    mods.insert("fs".to_string(), fs_mod);
    mods.insert("time".to_string(), time::create_time_module());
    mods.insert("env".to_string(), env::create_env_module());
    mods.insert("crypto".to_string(), crypto::create_crypto_module());
    mods.insert(
        "collections".to_string(),
        collections::create_collections_module(),
    );
    mods.insert("text".to_string(), text::create_text_module());
    mods.insert("random".to_string(), random::create_random_module());
    mods.insert("log".to_string(), log::create_log_module());
    mods.insert("jwt".to_string(), jwt::create_jwt_module());
    mods.insert("cache".to_string(), cache::create_cache_module());
    mods.insert(
        "validation".to_string(),
        validation::create_validation_module(),
    );
    mods.insert("db".to_string(), db::create_db_module());
    mods.insert("server".to_string(), server::create_server_module());
    mods.insert("http".to_string(), http::create_http_module());
    mods.insert("regex".to_string(), regex::load_regex_module());
    mods.insert("re".to_string(), regex::load_regex_module());
    mods.insert("os".to_string(), os::load_os_module());

    mods
}
