const editProfileButton = document.getElementById('editProfileButton');
const menuChangePassword = document.getElementById('menuChangePassword');
const menuNotifications = document.getElementById('menuNotifications');
const menuHelp = document.getElementById('menuHelp');
const menuAbout = document.getElementById('menuAbout');
const menuLogout = document.getElementById('menuLogout');
const photoUpload = document.getElementById('photoUpload');
const avatarImage = document.getElementById('avatarImage');
const modalAvatarImage = document.getElementById('modalAvatarImage');
const supportSuccess = document.getElementById('supportSuccess');
const profileSuccess = document.getElementById('profileSuccess');
const helpModal = document.getElementById('helpModal');
const aboutModal = document.getElementById('aboutModal');
const logoutModal = document.getElementById('logoutModal');
const editModal = document.getElementById('editModal');
const closeButtons = document.querySelectorAll('[data-close]');
const saveProfileButton = document.getElementById('saveProfile');
const helpButton = document.getElementById('sendSupport');
const confirmLogout = document.getElementById('confirmLogout');
const firstNameInput = document.getElementById('firstName');
const lastNameInput = document.getElementById('lastName');
const editEmailInput = document.getElementById('editEmail');
const editPhoneInput = document.getElementById('editPhone');

let pendingPhotoFile = null;

function openModal(modal) { modal.classList.remove('hidden'); }
function closeModal(modal) { modal.classList.add('hidden'); }

async function fetchProfile() {
  const res = await fetch('/api/profile');
  const j = await res.json();
  return j.user;
}

function setProfileData(user) {
  document.getElementById('displayName').textContent = user.name || 'Nexa User';
  document.getElementById('displayEmail').textContent = user.email || 'Not set';
  document.getElementById('displayPhone').textContent = user.phone || 'Not set';
  const [first = '', ...rest] = (user.name || '').split(' ');
  const last = rest.join(' ');
  firstNameInput.value = first;
  lastNameInput.value = last;
  editEmailInput.value = user.email || '';
  editPhoneInput.value = user.phone || '';
  avatarImage.src = user.photo || '/static/img/profile.png';
  modalAvatarImage.src = user.photo || '/static/img/profile.png';
}

function validateEmail(email) { return /\S+@\S+\.\S+/.test(email); }
function validatePhone(phone) { return !phone || /^\+?[0-9]{7,15}$/.test(phone); }

function openEditModal() {
  profileSuccess.classList.add('hidden');
  pendingPhotoFile = null;
  openModal(editModal);
}

editProfileButton.addEventListener('click', openEditModal);
menuHelp.addEventListener('click', () => openModal(helpModal));
menuAbout.addEventListener('click', () => openModal(aboutModal));
menuLogout.addEventListener('click', () => openModal(logoutModal));
menuChangePassword.addEventListener('click', () => alert('Change Password is coming soon.'));
menuNotifications.addEventListener('click', () => alert('Notification settings are coming soon.'));
closeButtons.forEach(btn => btn.addEventListener('click', () => closeModal(document.getElementById(btn.dataset.close))));

photoUpload.addEventListener('change', event => {
  const file = event.target.files[0];
  if (!file) return;
  if (!['image/jpeg', 'image/jpg', 'image/png', 'image/webp'].includes(file.type)) {
    alert('Allowed formats: JPG, PNG, WEBP.');
    return;
  }
  if (file.size > 5 * 1024 * 1024) {
    alert('File must be smaller than 5MB.');
    return;
  }
  pendingPhotoFile = file;
  const previewUrl = URL.createObjectURL(file);
  modalAvatarImage.src = previewUrl;
  avatarImage.src = previewUrl;
});

saveProfileButton.addEventListener('click', async () => {
  const firstName = firstNameInput.value.trim();
  const lastName = lastNameInput.value.trim();
  const email = editEmailInput.value.trim();
  const phone = editPhoneInput.value.trim();
  if (!firstName || !lastName || !email) {
    return alert('Please fill out all required fields.');
  }
  if (!validateEmail(email)) {
    return alert('Enter a valid email address.');
  }
  if (!validatePhone(phone)) {
    return alert('Enter a valid phone number.');
  }

  const profileRes = await fetch('/api/profile', {
    method: 'PUT',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ first_name: firstName, last_name: lastName, email, phone })
  });
  const profileJson = await profileRes.json();
  if (profileJson.error) {
    return alert(profileJson.error);
  }

  if (pendingPhotoFile) {
    const form = new FormData();
    form.append('photo', pendingPhotoFile);
    const uploadRes = await fetch('/api/profile/upload-photo', { method: 'POST', body: form });
    const uploadJson = await uploadRes.json();
    if (uploadJson.error) {
      return alert(uploadJson.error);
    }
  }

  profileSuccess.classList.remove('hidden');
  const user = await fetchProfile();
  setProfileData(user);
  setTimeout(() => closeModal(editModal), 750);
});

helpButton.addEventListener('click', async () => {
  const subject = document.getElementById('supportSubject').value.trim();
  const message = document.getElementById('supportMessage').value.trim();
  if (!subject || !message) {
    return alert('Subject and message are required.');
  }
  const res = await fetch('/api/support', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ subject, message })
  });
  const json = await res.json();
  if (json.error) {
    return alert(json.error);
  }
  supportSuccess.classList.remove('hidden');
});

confirmLogout.addEventListener('click', async () => {
  await fetch('/api/logout', { method: 'POST' });
  window.location.href = '/login';
});

(async () => {
  const user = await fetchProfile();
  if (!user) {
    window.location.href = '/login';
    return;
  }
  setProfileData(user);
})();
