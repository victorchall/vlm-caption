import React, { useState, useEffect } from 'react';
import './UpdateNotification.css';

const UpdateNotification = () => {
  const [updateStatus, setUpdateStatus] = useState('checking'); // checking, available, not-available, downloading, downloaded
  const [updateInfo, setUpdateInfo] = useState(null);
  const [downloadProgress, setDownloadProgress] = useState(0);

  useEffect(() => {
    // Listen for update events from main process
    window.api.receive('checking-for-update', () => {
      setUpdateStatus('checking');
    });

    window.api.receive('update-available', (info) => {
      setUpdateStatus('available');
      setUpdateInfo(info);
    });

    window.api.receive('update-not-available', () => {
      setUpdateStatus('not-available');
    });

    window.api.receive('download-progress', (progressObj) => {
      setUpdateStatus('downloading');
      setDownloadProgress(progressObj.percent);
    });

    window.api.receive('update-downloaded', () => {
      setUpdateStatus('downloaded');
    });

    window.api.receive('update-error', (error) => {
      console.error('Update error:', error);
      setUpdateStatus('error');
    });

    // Check for updates when component mounts
    window.api.send('check-for-updates');
  }, []);

  const handleCheckForUpdates = () => {
    window.api.send('check-for-updates');
  };

  const handleDownloadUpdate = () => {
    window.api.send('download-update');
  };

  const handleInstallUpdate = () => {
    window.api.send('quit-and-install');
  };

  if (updateStatus === 'checking') {
    return (
      <div className="update-notification checking">
        <span>Checking for updates...</span>
      </div>
    );
  }

  if (updateStatus === 'available') {
    return (
      <div className="update-notification available">
        <div className="update-content">
          <span>New version available: v{updateInfo.version}</span>
          <div className="update-buttons">
            <button onClick={handleDownloadUpdate}>Download Update</button>
            <button onClick={handleCheckForUpdates}>Check Again</button>
          </div>
        </div>
      </div>
    );
  }

  if (updateStatus === 'downloading') {
    return (
      <div className="update-notification downloading">
        <div className="update-content">
          <span>Downloading update... {Math.round(downloadProgress)}%</span>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${downloadProgress}%` }}></div>
          </div>
        </div>
      </div>
    );
  }

  if (updateStatus === 'downloaded') {
    return (
      <div className="update-notification downloaded">
        <div className="update-content">
          <span>Update downloaded and ready to install</span>
          <div className="update-buttons">
            <button onClick={handleInstallUpdate}>Install Now</button>
            <button onClick={handleCheckForUpdates}>Check Again</button>
          </div>
        </div>
      </div>
    );
  }

  if (updateStatus === 'error') {
    return (
      <div className="update-notification error">
        <div className="update-content">
          <span>Update check failed</span>
          <div className="update-buttons">
            <button onClick={handleCheckForUpdates}>Try Again</button>
          </div>
        </div>
      </div>
    );
  }

  // For 'not-available' status or default, show a minimal check button
  return (
    <div className="update-notification minimal">
      <button onClick={handleCheckForUpdates} className="check-updates-btn">
        Check for Updates
      </button>
    </div>
  );
};

export default UpdateNotification;
