use crate::values::{LyslynModule, Value};
use indexmap::IndexMap;
use std::cell::RefCell;
use std::rc::Rc;

struct DatabaseState {
    tables: IndexMap<String, Vec<IndexMap<String, Value>>>,
    auto_inc: IndexMap<String, i64>,
}

thread_local! {
    static DB_STATE: RefCell<DatabaseState> = RefCell::new(DatabaseState {
        tables: IndexMap::new(),
        auto_inc: IndexMap::new(),
    });
}

fn with_db<R>(f: impl FnOnce(&mut DatabaseState) -> R) -> R {
    DB_STATE.with(|cell| {
        let mut state = cell.borrow_mut();
        f(&mut state)
    })
}

fn row_matches_filter(row: &IndexMap<String, Value>, filter: &IndexMap<String, Value>) -> bool {
    for (k, v) in filter {
        match row.get(k) {
            Some(row_val) => {
                if row_val != v {
                    return false;
                }
            }
            None => return false,
        }
    }
    true
}

pub fn create_db_module() -> Value {
    let mut exports = IndexMap::new();

    exports.insert(
        "connect".to_string(),
        Value::NativeFunction(
            "connect".to_string(),
            Rc::new(|_| {
                with_db(|state| {
                    state.tables.clear();
                    state.auto_inc.clear();
                });
                Ok(Value::Nil)
            }),
        ),
    );

    exports.insert(
        "create_table".to_string(),
        Value::NativeFunction(
            "create_table".to_string(),
            Rc::new(|args| {
                if let Some(arg) = args.first() {
                    let tbl = arg.to_string();
                    with_db(|state| {
                        state.tables.entry(tbl).or_default();
                    });
                    Ok(Value::Bool(true))
                } else {
                    Err("Expected table name to db.create_table".to_string())
                }
            }),
        ),
    );

    exports.insert(
        "table_exists".to_string(),
        Value::NativeFunction(
            "table_exists".to_string(),
            Rc::new(|args| {
                if let Some(arg) = args.first() {
                    let tbl = arg.to_string();
                    let exists = with_db(|state| state.tables.contains_key(&tbl));
                    Ok(Value::Bool(exists))
                } else {
                    Err("Expected table name to db.table_exists".to_string())
                }
            }),
        ),
    );

    exports.insert(
        "insert".to_string(),
        Value::NativeFunction(
            "insert".to_string(),
            Rc::new(|args| {
                if args.len() >= 2 {
                    let tbl = args[0].to_string();
                    let row_map = match &args[1] {
                        Value::Map(m) => m.borrow().clone(),
                        _ => return Err("Expected row map to db.insert".to_string()),
                    };

                    let inserted_row = with_db(|state| {
                        let next_id = state.auto_inc.entry(tbl.clone()).or_insert(0);
                        *next_id += 1;
                        let id = *next_id;

                        let mut full_row = row_map;
                        if !full_row.contains_key("id") {
                            full_row.insert("id".to_string(), Value::Int(id));
                        }

                        let rows = state.tables.entry(tbl).or_default();
                        rows.push(full_row.clone());
                        full_row
                    });

                    Ok(Value::Map(Rc::new(RefCell::new(inserted_row))))
                } else {
                    Err("Expected table name and row map to db.insert".to_string())
                }
            }),
        ),
    );

    exports.insert(
        "count".to_string(),
        Value::NativeFunction(
            "count".to_string(),
            Rc::new(|args| {
                if let Some(arg) = args.first() {
                    let tbl = arg.to_string();
                    let cnt = with_db(|state| state.tables.get(&tbl).map(|r| r.len()).unwrap_or(0));
                    Ok(Value::Int(cnt as i64))
                } else {
                    Err("Expected table name to db.count".to_string())
                }
            }),
        ),
    );

    exports.insert(
        "find_one".to_string(),
        Value::NativeFunction(
            "find_one".to_string(),
            Rc::new(|args| {
                if args.len() >= 2 {
                    let tbl = args[0].to_string();
                    let filter = match &args[1] {
                        Value::Map(m) => m.borrow().clone(),
                        _ => return Err("Expected filter map to db.find_one".to_string()),
                    };

                    let found = with_db(|state| {
                        if let Some(rows) = state.tables.get(&tbl) {
                            for r in rows {
                                if row_matches_filter(r, &filter) {
                                    return Some(r.clone());
                                }
                            }
                        }
                        None
                    });

                    match found {
                        Some(row) => Ok(Value::Map(Rc::new(RefCell::new(row)))),
                        None => Ok(Value::Nil),
                    }
                } else {
                    Err("Expected table name and filter to db.find_one".to_string())
                }
            }),
        ),
    );

    exports.insert(
        "update".to_string(),
        Value::NativeFunction(
            "update".to_string(),
            Rc::new(|args| {
                if args.len() >= 3 {
                    let tbl = args[0].to_string();
                    let filter = match &args[1] {
                        Value::Map(m) => m.borrow().clone(),
                        _ => return Err("Expected filter map to db.update".to_string()),
                    };
                    let updates = match &args[2] {
                        Value::Map(m) => m.borrow().clone(),
                        _ => return Err("Expected updates map to db.update".to_string()),
                    };

                    let count = with_db(|state| {
                        let mut updated = 0;
                        if let Some(rows) = state.tables.get_mut(&tbl) {
                            for r in rows.iter_mut() {
                                if row_matches_filter(r, &filter) {
                                    for (k, v) in &updates {
                                        r.insert(k.clone(), v.clone());
                                    }
                                    updated += 1;
                                }
                            }
                        }
                        updated
                    });

                    Ok(Value::Int(count as i64))
                } else {
                    Err("Expected 3 arguments to db.update(table, filter, updates)".to_string())
                }
            }),
        ),
    );

    exports.insert(
        "delete".to_string(),
        Value::NativeFunction(
            "delete".to_string(),
            Rc::new(|args| {
                if args.len() >= 2 {
                    let tbl = args[0].to_string();
                    let filter = match &args[1] {
                        Value::Map(m) => m.borrow().clone(),
                        _ => return Err("Expected filter map to db.delete".to_string()),
                    };

                    let count = with_db(|state| {
                        if let Some(rows) = state.tables.get_mut(&tbl) {
                            let initial = rows.len();
                            rows.retain(|r| !row_matches_filter(r, &filter));
                            initial - rows.len()
                        } else {
                            0
                        }
                    });

                    Ok(Value::Int(count as i64))
                } else {
                    Err("Expected table name and filter to db.delete".to_string())
                }
            }),
        ),
    );

    exports.insert(
        "query".to_string(),
        Value::NativeFunction(
            "query".to_string(),
            Rc::new(|args| {
                if let Some(arg) = args.first() {
                    let sql = arg.to_string();
                    let params = if args.len() > 1 {
                        match &args[1] {
                            Value::List(l) => l.borrow().clone(),
                            _ => vec![args[1].clone()],
                        }
                    } else {
                        Vec::new()
                    };

                    let words: Vec<&str> = sql.split_whitespace().collect();
                    let from_pos = words.iter().position(|w| w.eq_ignore_ascii_case("FROM"));

                    let mut matched_rows = Vec::new();

                    if let Some(pos) = from_pos {
                        if pos + 1 < words.len() {
                            let table_name = words[pos + 1].trim_matches(';').to_string();
                            let where_pos =
                                words.iter().position(|w| w.eq_ignore_ascii_case("WHERE"));

                            with_db(|state| {
                                if let Some(rows) = state.tables.get(&table_name) {
                                    if let Some(w_pos) = where_pos {
                                        if w_pos + 1 < words.len() && !params.is_empty() {
                                            let col = words[w_pos + 1].to_string();
                                            let target_val = &params[0];
                                            for r in rows {
                                                if let Some(val) = r.get(&col) {
                                                    if val == target_val {
                                                        matched_rows.push(r.clone());
                                                    }
                                                }
                                            }
                                        } else {
                                            matched_rows = rows.clone();
                                        }
                                    } else {
                                        matched_rows = rows.clone();
                                    }
                                }
                            });
                        }
                    }

                    let val_list: Vec<Value> = matched_rows
                        .into_iter()
                        .map(|r| Value::Map(Rc::new(RefCell::new(r))))
                        .collect();
                    Ok(Value::List(Rc::new(RefCell::new(val_list))))
                } else {
                    Err("Expected SQL string to db.query".to_string())
                }
            }),
        ),
    );

    Value::Module(Rc::new(LyslynModule {
        name: "db".to_string(),
        exports: Rc::new(RefCell::new(exports)),
    }))
}
