/**
 * Recruiter Portal: Real-time JD AI analysis and Applicant Pipeline AJAX updates
 */

document.addEventListener('DOMContentLoaded', () => {
  // Real-time JD Skill Extraction
  const descTextarea = document.getElementById('job_description');
  const titleInput = document.getElementById('id_title');
  const previewBox = document.getElementById('ai-skill-preview-box');
  const detectedSkillsContainer = document.getElementById('detected-skills-container');
  const reqInput = document.getElementById('required_skills_input');
  const prefInput = document.getElementById('preferred_skills_input');

  let debounceTimer = null;

  if (descTextarea && detectedSkillsContainer) {
    const triggerAnalysis = () => {
      const text = descTextarea.value.trim();
      const title = titleInput ? titleInput.value.trim() : '';

      if (text.length < 30) {
        if (previewBox) previewBox.style.display = 'none';
        return;
      }

      fetch('/jobs/api/extract-skills/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ title: title, text: text })
      })
      .then(res => res.json())
      .then(data => {
        if (data.success && data.data) {
          const info = data.data;
          detectedSkillsContainer.innerHTML = '';
          if (previewBox) previewBox.style.display = 'block';

          // Auto-suggest skills
          if (info.all_skills && info.all_skills.length > 0) {
            info.all_skills.forEach(skill => {
              const chip = document.createElement('span');
              chip.className = 'tag-chip tag-matched';
              chip.style.cursor = 'pointer';
              chip.title = 'Click to add to required skills';
              chip.textContent = `+ ${skill}`;
              chip.addEventListener('click', () => {
                if (reqInput) {
                  const current = reqInput.value.split(',').map(s => s.trim()).filter(Boolean);
                  if (!current.includes(skill)) {
                    current.push(skill);
                    reqInput.value = current.join(', ');
                  }
                }
              });
              detectedSkillsContainer.appendChild(chip);
            });
          } else {
            detectedSkillsContainer.innerHTML = '<span class="text-muted" style="font-size: 0.85rem;">Keep typing description to detect technical skills...</span>';
          }
        }
      })
      .catch(err => console.error('Error analyzing JD:', err));
    };

    descTextarea.addEventListener('input', () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(triggerAnalysis, 700);
    });
  }

  // Pipeline Status Change Handler via AJAX
  const statusSelects = document.querySelectorAll('.pipeline-status-select');
  statusSelects.forEach(select => {
    select.addEventListener('change', (e) => {
      const appId = e.target.dataset.appId;
      const newStatus = e.target.value;
      const csrfToken = getCookie('csrftoken') ||
                        document.querySelector('[name=csrfmiddlewaretoken]')?.value;

      e.target.disabled = true;

      fetch(`/recruiter/api/applications/${appId}/status/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ status: newStatus })
      })
      .then(async res => {
        const isJson = res.headers.get('content-type')?.includes('application/json');
        const data = isJson ? await res.json() : null;
        if (!res.ok) {
          const errorMsg = data?.error || (res.status === 403 ? 'CSRF verification failed or unauthorized.' : `Server error (HTTP ${res.status})`);
          throw new Error(errorMsg);
        }
        return data;
      })
      .then(data => {
        if (data && data.success) {
          e.target.style.borderColor = '#10b981';
          setTimeout(() => {
            e.target.style.borderColor = '';
          }, 1500);
          if (data.status_changed && data.email_sent) {
            console.log(`Status updated to ${data.status_display}; email sent to ${data.student_email}`);
          }
        } else {
          alert('Error updating status: ' + (data?.error || 'Server error'));
        }
      })
      .catch(err => {
        console.error('Error updating status:', err);
        alert('Failed to update status: ' + err.message);
      })
      .finally(() => {
        e.target.disabled = false;
      });
    });
  });
});

