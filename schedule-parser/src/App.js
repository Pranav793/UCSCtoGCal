import React, { useState } from 'react';
import './App.css';
import api from './api'; // axios instance with baseURL, etc.

function App() {
  const [scheduleText, setScheduleText] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleDownloadICS = async () => {
    if (!scheduleText.trim()) {
      alert('Please paste your schedule text before parsing.');
      return;
    }
    setIsLoading(true);

    try {
      // We want to request the file as a BLOB (binary) so we can trigger a download
      const response = await api.post('/parseSchedule', 
        { scheduleText },
        { responseType: 'blob' }  // <-- important
      );
      // Now we have a blob of ICS data
      const blobUrl = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = blobUrl;
      link.setAttribute('download', 'my_schedule.ics'); // ICS filename
      document.body.appendChild(link);
      link.click();
      link.remove(); // cleanup
    } catch (err) {
      console.error('Error downloading ICS:', err);
      alert('Something went wrong while downloading the ICS file.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h2>UCSC Schedule to Calendar</h2>
        <p>Paste your schedule below, then download the ICS file.</p>
        <textarea
          rows={8}
          cols={60}
          placeholder="Paste UCSC schedule text here..."
          value={scheduleText}
          onChange={(e) => setScheduleText(e.target.value)}
        />
        <br />
        <button onClick={handleDownloadICS} disabled={isLoading}>
          {isLoading ? 'Downloading...' : 'Download Schedule File'}
        </button>
      </header>
    </div>
  );
}

export default App;
