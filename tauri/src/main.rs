// Audiobook Studio Tauri shell.
//
// On launch: spawn the Python FastAPI backend as a sidecar process,
// then load the Web UI in a native window pointing at 127.0.0.1.
// On quit: kill the backend process via Drop handler.

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use tauri::Manager;

struct BackendProcess(Mutex<Option<Child>>);

// Fix #7: implement Drop to kill backend on app exit
impl Drop for BackendProcess {
    fn drop(&mut self) {
        if let Ok(mut guard) = self.0.lock() {
            if let Some(mut child) = guard.take() {
                // Try graceful kill first, then force
                let _ = child.kill();
                let _ = child.wait();
                eprintln!("Backend process killed.");
            }
        }
    }
}

fn find_free_port() -> u16 {
    std::net::TcpListener::bind("127.0.0.1:0")
        .expect("Failed to bind for port discovery")
        .local_addr()
        .unwrap()
        .port()
}

fn spawn_backend(port: u16) -> Option<Child> {
    let candidates = [
        ("python3", vec!["-m", "uvicorn", "main:app", "--port"]),
        ("python", vec!["-m", "uvicorn", "main:app", "--port"]),
    ];

    let backend_dir = std::env::current_dir()
        .ok()
        .and_then(|p| p.parent().map(|p| p.join("backend")))
        .filter(|p| p.exists());

    for (cmd, args_prefix) in &candidates {
        let mut args = args_prefix.clone();
        args.push(&port.to_string());

        let mut cmd_builder = Command::new(cmd);
        cmd_builder.args(&args);

        if let Some(ref dir) = backend_dir {
            cmd_builder.current_dir(dir);
        }

        match cmd_builder
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .spawn()
        {
            Ok(child) => {
                eprintln!("Backend started on port {} (PID {})", port, child.id());
                return Some(child);
            }
            Err(_) => continue,
        }
    }

    eprintln!("WARNING: Could not start Python backend.");
    None
}

struct BackendPort(u16);

fn main() {
    let port = find_free_port();

    tauri::Builder::default()
        .manage(BackendProcess(Mutex::new(None)))
        .manage(BackendPort(port))
        .invoke_handler(tauri::generate_handler![backend_port])
        .setup(move |app| {
            if let Some(child) = spawn_backend(port) {
                let state: tauri::State<BackendProcess> = app.state();
                *state.0.lock().unwrap() = Some(child);
            }

            std::thread::sleep(std::time::Duration::from_secs(2));

            let url = format!("http://127.0.0.1:{}", port);
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.eval(&format!("window.location.href = '{}'", url));
            }

            Ok(())
        })
        .on_window_event(|event| {
            // When window is destroyed, the app exits and Drop runs automatically
            if let tauri::WindowEvent::Destroyed = event.event() {
                eprintln!("Window destroyed, shutting down...");
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

#[tauri::command]
fn backend_port(state: tauri::State<BackendPort>) -> u16 {
    state.0
}
