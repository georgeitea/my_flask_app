const socket = io();
const input = document.getElementById('titleInput');
const btn = document.getElementById('setTitleBtn');
const display = document.getElementById('titleDisplay');
const savedTitlesContainer = document.getElementById('savedTitles');
const volumeControl = document.getElementById('volumeControl');
const musicControls = document.getElementById('musicControls');
const volumeSlider = document.getElementById('volume');
const repeatBtn = document.getElementById('repeatBtn');

let savedSettings = {};
let currentTitle = null;

function renderSavedTitles() {
  savedTitlesContainer.innerHTML = '';
  for (const title in savedSettings) {
    const wrapper = document.createElement('div');
    wrapper.className = 'title-item';

    const btn = document.createElement('button');
    btn.textContent = title;
    btn.setAttribute('role', 'listitem');
    btn.className = 'title-button';
    btn.addEventListener('click', () => loadSettings(title));

    const menuBtn = document.createElement('button');
    menuBtn.className = 'menu-button';
    menuBtn.textContent = '⋮';
    menuBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      toggleMenu(wrapper);
    });

    const menu = document.createElement('div');
    menu.className = 'menu hidden';

    const renameBtn = document.createElement('button');
    renameBtn.textContent = 'Rename';
    renameBtn.addEventListener('click', () => {
      const newTitle = prompt('Enter new name:', title);
      if (newTitle && newTitle !== title && !savedSettings[newTitle]) {
        savedSettings[newTitle] = { ...savedSettings[title] };
        delete savedSettings[title];
        if (currentTitle === title) currentTitle = newTitle;
        renderSavedTitles();
        loadSettings(newTitle);
      }
    });

    const removeBtn = document.createElement('button');
    removeBtn.textContent = 'Remove';
    removeBtn.addEventListener('click', () => {
      const confirmDelete = confirm(`Διαγραφή του τίτλου "${title}" ;`);
      if (confirmDelete) {
        delete savedSettings[title];
        if (currentTitle === title) {
          currentTitle = null;
          display.textContent = '';
          volumeControl.classList.add('hidden');
          musicControls.classList.add('hidden');
          document.getElementById('repeatBtn').classList.add('hidden');
        }
        renderSavedTitles();
      }
    });

    menu.appendChild(renameBtn);
    menu.appendChild(removeBtn);

    wrapper.appendChild(btn);
    wrapper.appendChild(menuBtn);
    wrapper.appendChild(menu);
    savedTitlesContainer.appendChild(wrapper);
  }

  document.addEventListener('click', () => {
    document.querySelectorAll('.menu').forEach(m => m.classList.add('hidden'));
  });
}

function toggleMenu(wrapper) {
  const menu = wrapper.querySelector('.menu');
  document.querySelectorAll('.menu').forEach(m => {
    if (m !== menu) m.classList.add('hidden');
  });
  menu.classList.toggle('hidden');
}

function loadSettings(title) {
  currentTitle = title;
  display.textContent = title;
  volumeControl.classList.remove('hidden');
  musicControls.classList.remove('hidden');
  const settings = savedSettings[title];
  if (settings && settings.volume !== undefined) {
    volumeSlider.value = settings.volume;
    document.getElementById('repeatBtn').classList.remove('hidden');
  }
}

function saveSettings() {
  if (currentTitle) {
    savedSettings[currentTitle] = {
      ...savedSettings[currentTitle],
      volume: Number(volumeSlider.value),
    };
  }
}

function setTitle() {
  const val = input.value.trim();
  if (val.length > 0) {
    if (!savedSettings[val]) {
      savedSettings[val] = { volume: 50 };
    }
    renderSavedTitles();
    loadSettings(val);
    input.value = '';
  }
}

btn.addEventListener('click', setTitle);

input.addEventListener('keypress', e => {
  if (e.key === 'Enter') {
    setTitle();
  }
});

// Νέα Λογική για το Volume Slider
// Αποθηκεύει την τελευταία τιμή του slider
let lastVolumeValue = volumeSlider.value;

volumeSlider.addEventListener('input', () => {
  saveSettings();
  
  const currentVolumeValue = volumeSlider.value;
  
  if (currentVolumeValue > lastVolumeValue) {
    socket.emit('command', { command: 'volume_up' });
    console.log('Αποστολή εντολής: volume_up');
  } else if (currentVolumeValue < lastVolumeValue) {
    socket.emit('command', { command: 'volume_down' });
    console.log('Αποστολή εντολής: volume_down');
  }
  
  lastVolumeValue = currentVolumeValue;
});

// Νέα Λογική για τα κουμπιά μουσικής (περιλαμβάνει το repeat)
const musicButtons = document.querySelectorAll('.music-button');

musicButtons.forEach(button => {
  button.addEventListener('click', () => {
    const command = button.textContent.trim().toLowerCase();
    let commandToSend = '';

    if (command === 'start' || command === 'pause') {
      commandToSend = 'play_pause';
    } else if (command === 'volume up') {
      commandToSend = 'volume_up';
    } else if (command === 'volume down') {
      commandToSend = 'volume_down';
    } else if (command === 'repeat') {
      commandToSend = 'repeat';
    }

    if (commandToSend) {
      socket.emit('command', { command: commandToSend });
      console.log(`Αποστολή εντολής στον server: ${commandToSend}`);
    }
  });
});

// Προσθήκη νέου listener για το γεγονός server_stopped
socket.on('server_stopped', function(data) {
    alert(data.message); // Εμφάνιση του alert με το μήνυμα του server
    window.location.href = '/controller'; // Ανακατεύθυνση στην επιθυμητή σελίδα
});