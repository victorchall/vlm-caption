const { app, BrowserWindow, dialog } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const isDev = require('electron-is-dev');
const waitOn = require('wait-on');

let mainWindow;
let backendProcess;
const BACKEND_PORT = 5000;

// Create a log file for debugging
const logDir = path.join(app.getPath('userData'), 'logs');
if (!fs.existsSync(logDir)) {
  fs.mkdirSync(logDir, { recursive: true });
}
const logFile = path.join(logDir, 'electron-debug.log');

// Enhanced logging function
function log(message, level = 'INFO') {
  const timestamp = new Date().toISOString();
  const logMessage = `[${timestamp}] [${level}] ${message}\n`;
  
  // Write to file
  fs.appendFileSync(logFile, logMessage);
  
  // Also log to console (for development)
  console.log(`[${level}] ${message}`);
}

// Initialize log file
log('=== Electron App Starting ===');
log(`isDev: ${isDev}`);
log(`Log file location: ${logFile}`);

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      webSecurity: true
    },
    icon: path.join(__dirname, 'icon.ico'),
    show: false
  });

  // Load the React app
  const startUrl = isDev 
    ? 'http://localhost:3000' 
    : `file://${path.join(__dirname, '../build/index.html')}`;
  
  mainWindow.loadURL(startUrl);

  // Show window when ready to prevent visual flash
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  // Open DevTools in development
  if (isDev) {
    mainWindow.webContents.openDevTools();
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function startBackend() {
  return new Promise((resolve, reject) => {
    let backendPath;
    
    log('Starting backend process...');
    
    if (isDev) {
      // In development, run the Flask app directly
      backendPath = path.join(__dirname, '../../app.py');
      log(`Development mode: Starting Python Flask app at ${backendPath}`);
      log(`Working directory: ${path.join(__dirname, '../..')}`);
      backendProcess = spawn('python', [backendPath], {
        cwd: path.join(__dirname, '../..')
      });
    } else {
      // In production, run the packaged executable from resources directory
      const resourcesPath = process.resourcesPath;
      backendPath = path.join(resourcesPath, 'backend', 'app.exe');
      log(`Production mode: Starting executable at ${backendPath}`);
      log(`Working directory: ${path.join(resourcesPath, 'backend')}`);
      log(`Resources path: ${resourcesPath}`);
      
      // Check if the executable exists
      if (!fs.existsSync(backendPath)) {
        const error = new Error(`Backend executable not found at ${backendPath}`);
        log(`ERROR: ${error.message}`, 'ERROR');
        reject(error);
        return;
      }
      
      backendProcess = spawn(backendPath, [], {
        cwd: path.join(resourcesPath, 'backend')
      });
    }

    log(`Backend process spawned with PID: ${backendProcess.pid}`);

    backendProcess.stdout.on('data', (data) => {
      log(`Backend stdout: ${data.toString().trim()}`);
    });

    backendProcess.stderr.on('data', (data) => {
      log(`Backend stderr: ${data.toString().trim()}`, 'WARN');
    });

    backendProcess.on('error', (error) => {
      log(`Backend spawn error: ${error.message}`, 'ERROR');
      log(`Error code: ${error.code}`, 'ERROR');
      log(`Error path: ${error.path}`, 'ERROR');
      reject(error);
    });

    backendProcess.on('close', (code) => {
      log(`Backend process exited with code ${code}`, code === 0 ? 'INFO' : 'WARN');
    });

    // Wait for the backend to be ready
    // Use 127.0.0.1 instead of localhost to avoid DNS resolution issues
    log(`Waiting for backend to be ready at http://127.0.0.1:${BACKEND_PORT}/api/health`);
    waitOn({
      resources: [`http://127.0.0.1:${BACKEND_PORT}/api/health`],
      delay: 1000,
      interval: 100,
      timeout: 30000
    }).then(() => {
      log('Backend is ready and responding to health checks');
      resolve();
    }).catch((error) => {
      log(`Backend failed to start within timeout: ${error.message}`, 'ERROR');
      log(`waitOn error details: ${JSON.stringify(error)}`, 'ERROR');
      reject(error);
    });
  });
}

function stopBackend() {
  if (backendProcess && backendProcess.pid) {
    log(`Stopping backend process with PID: ${backendProcess.pid}...`);
    
    try {
      // On Windows, use taskkill to force terminate the process tree
      if (process.platform === 'win32') {
        log('Using Windows taskkill to terminate process tree...');
        const { execSync } = require('child_process');
        
        try {
          // Kill the entire process tree forcefully
          execSync(`taskkill /pid ${backendProcess.pid} /T /F`, { 
            stdio: 'ignore',
            timeout: 5000 
          });
          log('Backend process tree terminated successfully');
        } catch (taskkillError) {
          log(`Taskkill failed: ${taskkillError.message}`, 'WARN');
          
          // Fallback to Node.js kill
          try {
            backendProcess.kill('SIGKILL');
            log('Fallback SIGKILL sent to backend process');
          } catch (killError) {
            log(`Fallback kill failed: ${killError.message}`, 'WARN');
          }
        }
      } else {
        // On non-Windows platforms, use SIGKILL
        backendProcess.kill('SIGKILL');
        log('SIGKILL sent to backend process');
      }
      
      // Wait a moment for the process to terminate
      setTimeout(() => {
        if (backendProcess) {
          log('Backend process cleanup completed');
          backendProcess = null;
        }
      }, 1000);
      
    } catch (error) {
      log(`Error stopping backend process: ${error.message}`, 'ERROR');
    }
    
    backendProcess = null;
  } else {
    log('No backend process to stop');
  }
}

app.whenReady().then(async () => {
  try {
    log('App ready, starting backend...');
    // Start the backend first
    await startBackend();
    
    log('Backend started successfully, creating window...');
    // Then create the window
    createWindow();
    log('Window created successfully');
  } catch (error) {
    log(`Failed to start application: ${error.message}`, 'ERROR');
    log(`Error stack: ${error.stack}`, 'ERROR');
    
    // Show error dialog with log file location
    dialog.showErrorBox(
      'Startup Error', 
      `Failed to start the backend server.\n\nPlease check the logs at:\n${logFile}\n\nError: ${error.message}`
    );
    app.quit();
  }

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  log('All windows closed, stopping backend...');
  stopBackend();
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  log('App quitting, stopping backend...');
  stopBackend();
});

// Additional cleanup handlers for edge cases
app.on('will-quit', (event) => {
  log('App will quit, ensuring backend cleanup...');
  if (backendProcess && backendProcess.pid) {
    event.preventDefault();
    stopBackend();
    
    // Give some time for cleanup, then quit
    setTimeout(() => {
      app.quit();
    }, 2000);
  }
});

// Handle process exit signals
process.on('SIGINT', () => {
  log('Received SIGINT, stopping backend...');
  stopBackend();
  process.exit(0);
});

process.on('SIGTERM', () => {
  log('Received SIGTERM, stopping backend...');
  stopBackend();
  process.exit(0);
});

// Handle Windows-specific exit signals
if (process.platform === 'win32') {
  process.on('SIGBREAK', () => {
    log('Received SIGBREAK, stopping backend...');
    stopBackend();
    process.exit(0);
  });
}

// Handle any unhandled promise rejections
process.on('unhandledRejection', (reason, promise) => {
  log(`Unhandled Rejection at: ${promise}, reason: ${reason}`, 'ERROR');
});

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  log(`Uncaught Exception: ${error.message}`, 'ERROR');
  log(`Stack: ${error.stack}`, 'ERROR');
  stopBackend();
  process.exit(1);
});

// Ensure cleanup on process exit
process.on('exit', (code) => {
  log(`Process exiting with code: ${code}`);
  if (backendProcess && backendProcess.pid) {
    log('Force killing backend process on exit...');
    try {
      if (process.platform === 'win32') {
        require('child_process').execSync(`taskkill /pid ${backendProcess.pid} /T /F`, { 
          stdio: 'ignore',
          timeout: 3000 
        });
      } else {
        backendProcess.kill('SIGKILL');
      }
    } catch (err) {
      // Silent fail on exit
    }
  }
});
