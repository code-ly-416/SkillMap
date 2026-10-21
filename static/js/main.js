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
