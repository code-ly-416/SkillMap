function updateFileName(input) {
  if (input.files && input.files[0]) {
    const fileName = input.files[0].name;
    const display = document.getElementById('file-name-display');
    display.textContent = `Selected file: ${fileName}`;
    display.classList.remove('hidden');
  }
}

function showLoading() {
  const btn = document.getElementById('submit-btn');
  const spinner = document.getElementById('loading-spinner');

  if (btn) {
    btn.classList.add('btn-disabled');
    btn.disabled = true;
  }
  if (spinner) {
    spinner.classList.remove('hidden');
  }
}

// ---- Workspace page helpers ----

function toggleTopic(button) {
  button.closest('.topic-item').classList.toggle('done');
  updateProgress();
}

function updateProgress() {
  const items = document.querySelectorAll('.topic-item');
  const done = document.querySelectorAll('.topic-item.done');
  const bar = document.getElementById('progress-bar');
  const text = document.getElementById('progress-text');

  if (!bar || !text || items.length === 0) return;

  const pct = Math.round((done.length / items.length) * 100);
  bar.style.width = pct + '%';
  text.textContent = done.length + ' of ' + items.length + ' topics explored';
}

function filterTopics(query) {
  const q = query.toLowerCase();
  document.querySelectorAll('.topic-item').forEach(function (item) {
    const match = item.dataset.name.indexOf(q) !== -1;
    item.style.display = match ? '' : 'none';
  });
}

document.addEventListener('DOMContentLoaded', updateProgress);
