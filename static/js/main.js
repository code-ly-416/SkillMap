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

document.addEventListener('DOMContentLoaded', function () {
    updateProgress();

    document.querySelectorAll('.tree-card').forEach(function (card) {
        card.addEventListener('click', function () {
            const topic = card.getAttribute('data-topic');
            if (topic) openVideoPanel(topic);
        });
    });
});

// ---- Video resource panel ----

function openVideoPanel(topic) {
    const panel = document.getElementById('video-panel');
    if (!panel) return;

    panel.classList.remove('hidden');
    document.getElementById('video-topic-title').textContent = topic;

    const embed = document.getElementById('video-embed');
    const list = document.getElementById('video-list');
    embed.innerHTML = '';
    list.innerHTML = '';

    const loading = document.createElement('p');
    loading.className = 'video-loading';
    loading.textContent = 'Finding videos for "' + topic + '"...';
    embed.appendChild(loading);

    fetch('/api/videos?topic=' + encodeURIComponent(topic))
        .then(function (r) { return r.json(); })
        .then(function (videos) {
            embed.innerHTML = '';
            if (!videos.length) {
                const none = document.createElement('p');
                none.className = 'video-loading';
                none.textContent = 'No videos found. Check the server log and your API key.';
                embed.appendChild(none);
                return;
            }

            const first = videos[0];
            const iframe = document.createElement('iframe');
            iframe.width = '100%';
            iframe.height = '315';
            iframe.src = 'https://www.youtube.com/embed/' + first.video_id;
            iframe.title = first.title;
            iframe.allowFullscreen = true;
            embed.appendChild(iframe);

            videos.slice(1).forEach(function (v) {
                const item = document.createElement('button');
                item.className = 'video-item';
                item.type = 'button';
                item.onclick = function () {
                    iframe.src = 'https://www.youtube.com/embed/' + v.video_id;
                    embed.scrollIntoView({ behavior: 'smooth' });
                };

                const img = document.createElement('img');
                img.src = v.thumbnail;
                img.alt = v.title;

                const meta = document.createElement('span');
                meta.textContent = v.title + ' — ' + v.channel;

                item.appendChild(img);
                item.appendChild(meta);
                list.appendChild(item);
            });
        })
        .catch(function () {
            embed.innerHTML = '';
            const err = document.createElement('p');
            err.className = 'video-loading';
            err.textContent = 'Error loading videos.';
            embed.appendChild(err);
        });
}

function closeVideoPanel() {
    const panel = document.getElementById('video-panel');
    if (!panel) return;
    panel.classList.add('hidden');
    document.getElementById('video-embed').innerHTML = '';  // stops playback
    document.getElementById('video-list').innerHTML = '';
}
