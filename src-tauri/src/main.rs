// Prevents a console window from appearing on Windows in release builds
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::{Child, Command, Stdio};
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};
use tauri::{Manager, RunEvent, WebviewWindow};

/// Check if a TCP port is free.
fn is_port_free(port: u16) -> bool {
    std::net::TcpListener::bind(("127.0.0.1", port)).is_ok()
}

/// Find the first free port starting from `start` (searches up to +100).
fn find_free_port(start: u16) -> u16 {
    (start..start + 100)
        .find(|&p| is_port_free(p))
        .unwrap_or(start)
}

/// Poll Flask until it responds or timeout is reached.
fn wait_for_flask(url: &str, timeout: Duration) -> bool {
    let deadline = Instant::now() + timeout;
    while Instant::now() < deadline {
        if let Ok(resp) = ureq::get(url).call() {
            if resp.status() < 500 {
                return true;
            }
        }
        std::thread::sleep(Duration::from_millis(400));
    }
    false
}

/// Update the splash screen status text.
fn splash_status(window: &WebviewWindow, msg: &str) {
    let escaped = msg.replace('\\', "\\\\").replace('\'', "\\'");
    let _ = window.eval(&format!(
        "if(window.__setSplashStatus) window.__setSplashStatus('{}');",
        escaped
    ));
}

/// Show the first-run banner + start the star-catching game.
fn splash_first_run(window: &WebviewWindow) {
    let _ = window.eval("if(window.__showFirstRun) window.__showFirstRun();");
}

/// Show an error on the splash screen.
fn splash_error(window: &WebviewWindow, title: &str, detail: &str) {
    let t = title.replace('`', "'");
    let d = detail.replace('`', "'").replace('\n', "<br>");
    let _ = window.eval(&format!(
        r#"document.body.innerHTML = `
            <div style="background:#1a1a2e;color:#eee;height:100vh;display:flex;
                        align-items:center;justify-content:center;font-family:sans-serif;
                        text-align:center;padding:40px">
                <div>
                    <h2 style="color:#c0392b">{}</h2>
                    <p style="max-width:500px;line-height:1.6">{}</p>
                </div>
            </div>`;"#,
        t, d
    ));
}

/// Parse "Python X.Y.Z" output into (major, minor).
fn parse_python_version(output: &[u8]) -> Option<(u32, u32)> {
    let text = String::from_utf8_lossy(output);
    let version_part = text.strip_prefix("Python ")?;
    let mut parts = version_part.trim().split('.');
    let major = parts.next()?.parse::<u32>().ok()?;
    let minor = parts.next()?.parse::<u32>().ok()?;
    Some((major, minor))
}

/// Resolve a Python >= 3.10 executable, searching PATH and well-known locations.
fn resolve_system_python() -> String {
    let well_known: &[&str] = &[
        "/opt/homebrew/bin/python3",
        "/usr/local/bin/python3",
        "/opt/homebrew/bin/python3.14",
        "/opt/homebrew/bin/python3.13",
        "/opt/homebrew/bin/python3.12",
        "/opt/homebrew/bin/python3.11",
        "/opt/homebrew/bin/python3.10",
        "/usr/local/bin/python3.14",
        "/usr/local/bin/python3.13",
        "/usr/local/bin/python3.12",
        "/usr/local/bin/python3.11",
        "/usr/local/bin/python3.10",
    ];

    for candidate in well_known {
        if let Ok(out) = Command::new(candidate).arg("--version").output() {
            if out.status.success() {
                if let Some((major, minor)) = parse_python_version(&out.stdout) {
                    if major == 3 && minor >= 10 {
                        println!("Found Python {}.{} at {}", major, minor, candidate);
                        return candidate.to_string();
                    }
                }
            }
        }
    }

    for candidate in &["python3", "python"] {
        if let Ok(out) = Command::new(candidate).arg("--version").output() {
            if out.status.success() {
                if let Some((major, minor)) = parse_python_version(&out.stdout) {
                    if major == 3 && minor >= 10 {
                        println!("Found Python {}.{} via PATH as '{}'", major, minor, candidate);
                        return candidate.to_string();
                    }
                }
            }
        }
    }

    eprintln!("Warning: could not find Python >= 3.10");
    "python3".to_string()
}

/// Copy bundled client files to a writable directory so Flask can run there.
/// Only copies if the destination is missing or the app version changed.
fn sync_client_to_runtime(
    bundle_client: &std::path::Path,
    runtime_client: &std::path::Path,
    app_version: &str,
) -> bool {
    let stamp = runtime_client.join(".version_stamp");
    let current = std::fs::read_to_string(&stamp).unwrap_or_default();

    // Skip if already synced for this version
    if current.trim() == app_version && runtime_client.join("app.py").exists() {
        println!("Runtime client already synced (v{})", app_version);
        return true;
    }

    println!(
        "Syncing client files from bundle to runtime:\n  {} → {}",
        bundle_client.display(),
        runtime_client.display()
    );

    let _ = std::fs::create_dir_all(runtime_client);

    // Copy key files (preserving what the user might have changed like config.json)
    let files_to_copy = ["app.py", "requirements.txt", "start.sh"];
    for name in &files_to_copy {
        let src = bundle_client.join(name);
        let dst = runtime_client.join(name);
        if src.exists() {
            if let Err(e) = std::fs::copy(&src, &dst) {
                eprintln!("Failed to copy {}: {}", name, e);
                return false;
            }
        }
    }

    // Copy config.json only if it doesn't exist yet (preserve user edits)
    let config_dst = runtime_client.join("config.json");
    if !config_dst.exists() {
        let config_src = bundle_client.join("config.json");
        if config_src.exists() {
            let _ = std::fs::copy(&config_src, &config_dst);
        }
    }

    // Copy templates directory (always overwrite — these are app code)
    let tmpl_src = bundle_client.join("templates");
    let tmpl_dst = runtime_client.join("templates");
    if tmpl_src.exists() {
        let _ = std::fs::create_dir_all(&tmpl_dst);
        if let Ok(entries) = std::fs::read_dir(&tmpl_src) {
            for entry in entries.flatten() {
                let dst_file = tmpl_dst.join(entry.file_name());
                let _ = std::fs::copy(entry.path(), dst_file);
            }
        }
    }

    // Create writable directories that Flask needs
    let _ = std::fs::create_dir_all(runtime_client.join("logs"));
    let _ = std::fs::create_dir_all(runtime_client.join("projects"));

    // Write version stamp
    let _ = std::fs::write(&stamp, app_version);
    true
}

/// Ensure a venv exists at `venv_dir`, creating and populating it if needed.
fn ensure_venv(
    venv_dir: &std::path::Path,
    requirements_txt: &std::path::Path,
    system_python: &str,
    window: Option<&WebviewWindow>,
) -> Result<String, String> {
    #[cfg(windows)]
    let venv_python = venv_dir.join("Scripts").join("python.exe");
    #[cfg(not(windows))]
    let venv_python = venv_dir.join("bin").join("python");

    if venv_python.exists() {
        // Sanity check: can the venv python import flask?
        let check = Command::new(&venv_python)
            .args(&["-c", "import flask"])
            .output();
        if check.map(|o| o.status.success()).unwrap_or(false) {
            return Ok(venv_python.to_string_lossy().into_owned());
        }
        println!("Venv exists but flask is missing — recreating...");
        let _ = std::fs::remove_dir_all(venv_dir);
    }

    // This is a first-run install
    if let Some(w) = window {
        splash_first_run(w);
        splash_status(w, "Creating virtual environment . . .");
    }

    println!("Creating virtual environment at: {}", venv_dir.display());
    let _ = std::fs::create_dir_all(venv_dir);

    let status = Command::new(system_python)
        .args(&["-m", "venv"])
        .arg(venv_dir)
        .status();

    if !status.map(|s| s.success()).unwrap_or(false) || !venv_python.exists() {
        return Err(format!(
            "Failed to create virtual environment.\n\nPython used: {}\nTarget: {}",
            system_python,
            venv_dir.display()
        ));
    }

    if requirements_txt.exists() {
        if let Some(w) = window {
            splash_status(w, "Installing packages . . .");
        }

        #[cfg(windows)]
        let pip = venv_dir.join("Scripts").join("pip.exe");
        #[cfg(not(windows))]
        let pip = venv_dir.join("bin").join("pip");

        println!("Installing dependencies from: {}", requirements_txt.display());
        let pip_result = Command::new(&pip)
            .args(&["install", "-q", "-r"])
            .arg(requirements_txt)
            .stderr(Stdio::piped())
            .output();

        match pip_result {
            Ok(output) if !output.status.success() => {
                let stderr = String::from_utf8_lossy(&output.stderr);
                eprintln!("pip install failed:\n{}", stderr);
                // Clean up the broken venv
                let _ = std::fs::remove_dir_all(venv_dir);
                return Err(format!(
                    "Failed to install Python packages.\n\n{}",
                    stderr.lines().take(8).collect::<Vec<_>>().join("\n")
                ));
            }
            Err(e) => {
                let _ = std::fs::remove_dir_all(venv_dir);
                return Err(format!("Could not run pip: {}", e));
            }
            _ => {}
        }
    }

    Ok(venv_python.to_string_lossy().into_owned())
}

fn main() {
    let flask_child: Arc<Mutex<Option<Child>>> = Arc::new(Mutex::new(None));
    let flask_child_clone = flask_child.clone();

    tauri::Builder::default()
        .setup(move |app| {
            let app_handle = app.handle().clone();

            // Locate bundled client files (read-only in production).
            let resource_dir = app_handle.path().resource_dir().unwrap_or_default();
            let bundle_client_dir = if cfg!(debug_assertions) {
                std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR"))
                    .parent()
                    .unwrap()
                    .join("client")
            } else {
                resource_dir.join("_up_").join("client")
            };

            if !bundle_client_dir.exists() {
                eprintln!(
                    "Could not find the client directory at:\n{}",
                    bundle_client_dir.display()
                );
                std::process::exit(1);
            }

            // In dev mode, run Flask directly from client/ (already writable).
            // In production, copy client files to a writable location first.
            let client_dir = if cfg!(debug_assertions) {
                bundle_client_dir.clone()
            } else {
                let runtime_base = app_handle
                    .path()
                    .app_data_dir()
                    .unwrap_or_else(|_| bundle_client_dir.clone());
                let runtime_client = runtime_base.join("client");
                let version = env!("CARGO_PKG_VERSION");
                sync_client_to_runtime(&bundle_client_dir, &runtime_client, version);
                runtime_client
            };

            let port = find_free_port(5001);
            let flask_url = format!("http://127.0.0.1:{}", port);

            // Show the splash screen immediately.
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.show();
            }

            // Background thread: set up venv, spawn Flask, navigate on ready.
            let flask_url_clone = flask_url.clone();
            std::thread::spawn(move || {
                let splash_start = Instant::now();
                let min_splash = Duration::from_secs(5);
                let window = app_handle.get_webview_window("main");

                if let Some(w) = &window {
                    splash_status(w, "Locating Python . . .");
                }

                let python = if cfg!(debug_assertions) {
                    // Dev: use existing venv or system python
                    #[cfg(windows)]
                    let venv_py = client_dir.join("venv").join("Scripts").join("python.exe");
                    #[cfg(not(windows))]
                    let venv_py = client_dir.join("venv").join("bin").join("python");

                    if venv_py.exists() {
                        venv_py.to_string_lossy().into_owned()
                    } else {
                        resolve_system_python()
                    }
                } else {
                    let system_python = resolve_system_python();
                    let venv_dir = client_dir.join("venv");
                    let requirements_txt = client_dir.join("requirements.txt");
                    match ensure_venv(
                        &venv_dir,
                        &requirements_txt,
                        &system_python,
                        window.as_ref(),
                    ) {
                        Ok(py) => py,
                        Err(msg) => {
                            eprintln!("{}", msg);
                            if let Some(w) = &window {
                                splash_error(w, "Setup failed", &msg);
                            }
                            return;
                        }
                    }
                };

                if let Some(w) = &window {
                    splash_status(w, "Starting backend . . .");
                }

                println!("Starting Flask on port {} using Python: {}", port, python);
                println!("Client directory: {}", client_dir.display());

                let child = Command::new(&python)
                    .arg("app.py")
                    .current_dir(&client_dir)
                    .env("PORT", port.to_string())
                    .env("FLASK_DEBUG", "0")
                    .env("PATH", std::env::var("PATH").unwrap_or_default())
                    .stderr(Stdio::piped())
                    .spawn();

                match child {
                    Ok(mut c) => {
                        // Grab stderr handle before moving child into the mutex
                        let stderr = c.stderr.take();
                        *flask_child_clone.lock().unwrap() = Some(c);

                        // Log Flask stderr in a side thread so we can see errors
                        if let Some(stderr) = stderr {
                            std::thread::spawn(move || {
                                use std::io::BufRead;
                                let reader = std::io::BufReader::new(stderr);
                                for line in reader.lines() {
                                    if let Ok(line) = line {
                                        eprintln!("[flask] {}", line);
                                    }
                                }
                            });
                        }
                    }
                    Err(e) => {
                        eprintln!("Failed to start Flask: {}", e);
                        if let Some(w) = &window {
                            splash_error(
                                w,
                                "Backend failed to launch",
                                &format!(
                                    "Could not start Python backend.\n\nPython: {}\nError: {}\n\nMake sure Python 3.10+ is installed.",
                                    python, e
                                ),
                            );
                        }
                        return;
                    }
                }

                if let Some(w) = &window {
                    splash_status(w, "Waiting for backend . . .");
                }

                let ready = wait_for_flask(&flask_url_clone, Duration::from_secs(120));

                if let Some(w) = &window {
                    if ready {
                        // Let the owl have its moment
                        let elapsed = splash_start.elapsed();
                        if elapsed < min_splash {
                            splash_status(w, "Almost ready . . .");
                            std::thread::sleep(min_splash - elapsed);
                        }
                        let _ = w.eval("if(window.__stopGame) window.__stopGame();");
                        let _ = w.eval(&format!(
                            "window.location.href = '{}';",
                            flask_url_clone
                        ));
                    } else {
                        // Check if Flask process died
                        let mut extra = String::new();
                        if let Ok(guard) = flask_child_clone.lock() {
                            if guard.is_none() {
                                extra = "The Python process exited unexpectedly.\n\n".to_string();
                            }
                        }
                        splash_error(
                            w,
                            "Backend did not start",
                            &format!(
                                "{}The Python backend took too long to start.\n\nCheck the console log for errors.\nTry running client/start.sh in a terminal first.",
                                extra
                            ),
                        );
                    }
                }
            });

            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(move |_app_handle, event| {
            if let RunEvent::Exit = event {
                if let Ok(mut guard) = flask_child.lock() {
                    if let Some(mut child) = guard.take() {
                        #[cfg(unix)]
                        {
                            unsafe { libc::kill(child.id() as i32, libc::SIGTERM) };
                            std::thread::sleep(Duration::from_millis(1500));
                        }
                        let _ = child.kill();
                        let _ = child.wait();
                    }
                }
            }
        });
}
