import React, { useState } from 'react';
import './App.css';
import api from './api'; // axios instance with baseURL, etc.
import textImg from './assets/highlightedtext.png'

function App() {
  const [scheduleText, setScheduleText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showInstructions, setShowInstructions] = useState(false);

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
        <h1>UCSC Schedule to Calendar</h1>

        {/* Button that toggles the instructions popup */}
        <button onClick={() => setShowInstructions(!showInstructions)}>
          Show Instructions
        </button>

        {showInstructions && (
          <div className="instructions-popup">
            <div className="instructions-content">
              <h4>How to Get Your UCSC Schedule Text</h4>
              <p>
                1. Log in to your UCSC student portal.<br />
                2. Go to your Enrollment page and highlight and copy the text as shown below.<br />
              </p>   
              <img src={textImg} alt="Instructions" />
              <p>
                3. Paste the schedule text into the box below.<br />
              </p>
              <button onClick={() => setShowInstructions(false)}>Close</button>
            </div>
          </div>
        )}


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
