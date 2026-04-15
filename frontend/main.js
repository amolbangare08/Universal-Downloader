const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn, execSync } = require('child_process');

let mainWindow;
let childProcess = null;

// --- Detect Python executable ---
function getPythonCommand() {
  for (const cmd of ['python3', 'python']) {
    try {
      const version = execSync(`${cmd} --version`, { encoding: 'utf-8', timeout: 5000 });
      if (version.includes('Python 3')) {
        return cmd;
      }
    } catch (_e) {
      // Try next candidate
    }
  }
  return 'python'; // fallback
}

const pythonCmd = getPythonCommand();

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 850,
    height: 850,
    title: "Universal Downloader",
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    }
  });

  mainWindow.loadFile('index.html');
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

// --- Kill child process on quit ---
app.on('will-quit', () => {
  if (childProcess) {
    try { childProcess.kill(); } catch (_e) { /* already exited */ }
    childProcess = null;
  }
});

// --- START DOWNLOAD ---
ipcMain.on('start-download', async (event, args) => {
  const { url, mode, res, audio_fmt, use_hb, hb_preset, trim_on, t_start, t_end } = args;

  const scriptPath = path.join(__dirname, '..', 'backend', 'cli.py');

  // 1. Select Folder
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openDirectory'],
    title: 'Select Download Folder'
  });

  if (result.canceled) {
    mainWindow.webContents.send('download-canceled');
    return;
  }

  const folder = result.filePaths[0];

  // 2. Prepare Arguments
  const cliArgs = [
    scriptPath,
    url,
    '--folder', folder,
    '--mode', mode,
    '--res', res,
    '--audio_fmt', audio_fmt,
    '--hb_preset', hb_preset
  ];

  if (use_hb) cliArgs.push('--use_hb');
  if (trim_on) {
    cliArgs.push('--trim_on');
    cliArgs.push('--trim_start', t_start);
    cliArgs.push('--trim_end', t_end);
  }

  // 3. Spawn Python
  if (childProcess) {
    try { childProcess.kill(); } catch (_e) { /* already exited */ }
  }

  childProcess = spawn(pythonCmd, cliArgs);

  // 4. Listen for Output
  childProcess.stdout.on('data', (data) => {
    const lines = data.toString().split('\n');
    lines.forEach(line => {
      if (!line.trim()) return;
      try {
        const json = JSON.parse(line);
        mainWindow.webContents.send('python-output', json);
      } catch (_e) {
        // Ignore non-JSON output
      }
    });
  });

  childProcess.stderr.on('data', (data) => {
    console.error(`Python Error: ${data}`);
  });

  childProcess.on('close', (_code) => {
    childProcess = null;
  });
});

// --- STOP DOWNLOAD ---
ipcMain.on('stop-download', () => {
  if (childProcess) {
    childProcess.kill();
    childProcess = null;
  }
  mainWindow.webContents.send('download-stopped');
});
