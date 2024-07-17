// toggle input fields
function toggleForm() {
  const issueType = document.getElementById('issueType').value;
  const forms = document.querySelectorAll('.issue-form');

  forms.forEach(form => {
    if (form.id === `${issueType}Form`) {
      form.classList.remove('hidden');
    } else {
      form.classList.add('hidden');
    }
  });
}
