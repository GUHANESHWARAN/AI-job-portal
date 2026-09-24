/**
 * Student portal interactions: Drag-drop resume, skill-gap dynamic selectors
 */

document.addEventListener('DOMContentLoaded', () => {
  // Dropzone file upload enhancement
  const dropzone = document.getElementById('resume-dropzone');
  const fileInput = document.getElementById('id_resume_file');
  const fileNameDisplay = document.getElementById('selected-file-name');

  if (dropzone && fileInput) {
    dropzone.addEventListener('click', () => fileInput.click());

    ['dragenter', 'dragover'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.add('dragover');
      });
    });

    ['dragleave', 'drop'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.remove('dragover');
      });
    });

    dropzone.addEventListener('drop', (e) => {
      const dt = e.dataTransfer;
      const files = dt.files;
      if (files.length > 0) {
        fileInput.files = files;
        if (fileNameDisplay) {
          fileNameDisplay.textContent = `Selected: ${files[0].name} (${Math.round(files[0].size / 1024)} KB)`;
        }
      }
    });

    fileInput.addEventListener('change', () => {
      if (fileInput.files.length > 0 && fileNameDisplay) {
        fileNameDisplay.textContent = `Selected: ${fileInput.files[0].name} (${Math.round(fileInput.files[0].size / 1024)} KB)`;
      }
    });
  }

  // Skill Gap mode switcher
  const modeRadios = document.querySelectorAll('input[name="skill_gap_mode"]');
  const benchmarkSelect = document.getElementById('benchmark-select-group');
  const jobSelect = document.getElementById('job-select-group');

  if (modeRadios.length > 0) {
    modeRadios.forEach(radio => {
      radio.addEventListener('change', (e) => {
        if (e.target.value === 'benchmark') {
          if (benchmarkSelect) benchmarkSelect.style.display = 'block';
          if (jobSelect) jobSelect.style.display = 'none';
        } else {
          if (benchmarkSelect) benchmarkSelect.style.display = 'none';
          if (jobSelect) jobSelect.style.display = 'block';
        }
      });
    });
  }
});

