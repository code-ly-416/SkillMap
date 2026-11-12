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
  saveTopicProgress();
}

function saveTopicProgress() {
  const mainEl = document.querySelector('main[data-roadmap-id]');
  if (!mainEl) return;
  const roadmapId = mainEl.dataset.roadmapId;

  const done = Array.from(document.querySelectorAll('.topic-item.done')).map(function (item) {
    return item.dataset.topicKey;
  });

  fetch('/api/progress/' + roadmapId, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ topics: done })
  }).catch(function () {});
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

// ---- Quiz panel ----

let quizState = null;

function closeQuizPanel() {
    const panel = document.getElementById('quiz-panel');
    if (!panel) return;
    panel.classList.add('hidden');
    document.getElementById('quiz-body').innerHTML = '';
    document.getElementById('quiz-title').textContent = 'Quiz';
    quizState = null;
}

async function openQuizPanel(moduleIndex) {
    const panel = document.getElementById('quiz-panel');
    const body = document.getElementById('quiz-body');
    if (!panel || !body) return;

    const mainEl = document.querySelector('main[data-roadmap-id]');
    if (!mainEl) return;
    const roadmapId = mainEl.dataset.roadmapId;

    panel.classList.remove('hidden');
    body.innerHTML = '';
    document.getElementById('quiz-title').textContent = 'Generating quiz...';

    const loading = document.createElement('p');
    loading.className = 'quiz-loading';
    loading.textContent = 'Generating 5 questions with AI... (this can take up to a minute)';
    body.appendChild(loading);

    try {
        const res = await fetch('/api/quiz/' + roadmapId, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ module_index: moduleIndex })
        });
        const quiz = await res.json();
        if (!res.ok || quiz.error) {
            body.innerHTML = '';
            const err = document.createElement('p');
            err.className = 'quiz-loading';
            err.textContent = quiz.error || 'Error generating quiz.';
            body.appendChild(err);
            document.getElementById('quiz-title').textContent = 'Quiz';
            return;
        }

        quizState = { roadmapId: roadmapId, moduleIndex: moduleIndex, quiz: quiz };
        document.getElementById('quiz-title').textContent = 'Quiz: ' + quiz.module_title;
        renderQuizQuestions();
    } catch (e) {
        body.innerHTML = '';
        const err = document.createElement('p');
        err.className = 'quiz-loading';
        err.textContent = 'Error contacting the server.';
        body.appendChild(err);
    }
}

function renderQuizQuestions() {
    const body = document.getElementById('quiz-body');
    body.innerHTML = '';

    quizState.quiz.questions.forEach(function (q, i) {
        const block = document.createElement('div');
        block.className = 'quiz-question';

        const heading = document.createElement('p');
        heading.className = 'quiz-q-text';
        heading.textContent = (i + 1) + '. ' + q.question;
        block.appendChild(heading);

        q.options.forEach(function (opt, oi) {
            const label = document.createElement('label');
            label.className = 'quiz-option';

            const radio = document.createElement('input');
            radio.type = 'radio';
            radio.name = 'q' + i;
            radio.value = oi;

            const text = document.createElement('span');
            text.textContent = opt;

            label.appendChild(radio);
            label.appendChild(text);
            block.appendChild(label);
        });

        body.appendChild(block);
    });

    const submit = document.createElement('button');
    submit.type = 'button';
    submit.className = 'quiz-submit';
    submit.textContent = 'Submit answers';
    submit.onclick = submitQuiz;
    body.appendChild(submit);
}

async function submitQuiz() {
    if (!quizState) return;

    const answers = quizState.quiz.questions.map(function (q, i) {
        const selected = document.querySelector('input[name="q' + i + '"]:checked');
        return selected ? parseInt(selected.value, 10) : -1;
    });

    if (answers.indexOf(-1) !== -1) {
        alert('Please answer all the questions before submitting.');
        return;
    }

    const body = document.getElementById('quiz-body');
    body.innerHTML = '';
    const loading = document.createElement('p');
    loading.className = 'quiz-loading';
    loading.textContent = 'Evaluating your answers...';
    body.appendChild(loading);

    try {
        const res = await fetch('/api/quiz/' + quizState.roadmapId + '/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ module_index: quizState.moduleIndex, answers: answers })
        });
        const result = await res.json();
        if (!res.ok || result.error) {
            body.innerHTML = '';
            const err = document.createElement('p');
            err.className = 'quiz-loading';
            err.textContent = result.error || 'Error evaluating the quiz.';
            body.appendChild(err);
            return;
        }
        renderQuizResults(result);
    } catch (e) {
        body.innerHTML = '';
        const err = document.createElement('p');
        err.className = 'quiz-loading';
        err.textContent = 'Error contacting the server.';
        body.appendChild(err);
    }
}

function renderQuizResults(result) {
    const body = document.getElementById('quiz-body');
    body.innerHTML = '';

    // Score
    const head = document.createElement('div');
    head.className = 'quiz-score-head';
    const score = document.createElement('p');
    score.className = 'quiz-score';
    score.textContent = result.score + ' / ' + result.total;
    const scoreLabel = document.createElement('p');
    scoreLabel.className = 'quiz-score-label';
    scoreLabel.textContent = 'Your score';
    head.appendChild(score);
    head.appendChild(scoreLabel);
    body.appendChild(head);

    // Weak / strong areas (learner model insight)
    const insights = document.createElement('div');
    insights.className = 'quiz-insights';

    const weakBox = document.createElement('div');
    weakBox.className = 'quiz-insight-box quiz-insight-weak';
    const weakTitle = document.createElement('h4');
    weakTitle.textContent = 'Needs revision';
    weakBox.appendChild(weakTitle);
    const weakItems = result.weak_topics.length ? result.weak_topics : ['None — great job!'];
    weakItems.forEach(function (t) {
        const p = document.createElement('p');
        p.textContent = t;
        weakBox.appendChild(p);
    });

    const strongBox = document.createElement('div');
    strongBox.className = 'quiz-insight-box quiz-insight-strong';
    const strongTitle = document.createElement('h4');
    strongTitle.textContent = 'Strong areas';
    strongBox.appendChild(strongTitle);
    const strongItems = result.strong_topics.length ? result.strong_topics : ['None yet'];
    strongItems.forEach(function (t) {
        const p = document.createElement('p');
        p.textContent = t;
        strongBox.appendChild(p);
    });

    insights.appendChild(weakBox);
    insights.appendChild(strongBox);
    body.appendChild(insights);

    // Per-question breakdown
    result.results.forEach(function (r, i) {
        const block = document.createElement('div');
        block.className = 'quiz-result-item ' + (r.correct ? 'quiz-correct' : 'quiz-wrong');

        const heading = document.createElement('p');
        heading.className = 'quiz-q-text';
        heading.textContent = (i + 1) + '. ' + r.question;
        block.appendChild(heading);

        const answer = document.createElement('p');
        answer.className = 'quiz-answer';
        answer.textContent = 'Your answer: ' + (r.chosen || '—') + (r.correct ? ' ✓' : '  ·  Correct answer: ' + r.correct_answer);
        block.appendChild(answer);

        if (r.explanation) {
            const explanation = document.createElement('p');
            explanation.className = 'quiz-explanation';
            explanation.textContent = r.explanation;
            block.appendChild(explanation);
        }

        body.appendChild(block);
    });

    // Retry (adaptive: next generation will be harder)
    const retry = document.createElement('button');
    retry.type = 'button';
    retry.className = 'quiz-submit';
    retry.textContent = 'Retry quiz (harder questions)';
    retry.onclick = function () { openQuizPanel(quizState.moduleIndex); };
    body.appendChild(retry);
}
