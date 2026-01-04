const slides = document.querySelectorAll('.slide');
const dotsContainer = document.querySelector('.dots');
const prev = document.querySelector('.prev');
const next = document.querySelector('.next');
let current = 0;
let interval;
let touchStartX = 0;

// Create dots dynamically
slides.forEach((_, i) => {
  const dot = document.createElement('span');
  dot.addEventListener('click', () => goToSlide(i));
  dotsContainer.appendChild(dot);
});

function updateSlides() {
  slides.forEach((slide, i) => {
    slide.classList.toggle('active', i === current);
    dotsContainer.children[i].classList.toggle('active', i === current);
  });
}

function goToSlide(index) {
  current = (index + slides.length) % slides.length;
  updateSlides();
}

function nextSlide() {
  goToSlide(current + 1);
}

function prevSlide() {
  goToSlide(current - 1);
}

function startAutoSlide() {
  interval = setInterval(nextSlide, 4000);
}

function stopAutoSlide() {
  clearInterval(interval);
}

// Touch (swipe) support
document.querySelector('.carousel-container').addEventListener('touchstart', e => {
  touchStartX = e.touches[0].clientX;
});
document.querySelector('.carousel-container').addEventListener('touchend', e => {
  const touchEndX = e.changedTouches[0].clientX;
  if (touchEndX < touchStartX - 50) nextSlide();
  if (touchEndX > touchStartX + 50) prevSlide();
});

next.addEventListener('click', nextSlide);
prev.addEventListener('click', prevSlide);
document.querySelector('.carousel-container').addEventListener('mouseenter', stopAutoSlide);
document.querySelector('.carousel-container').addEventListener('mouseleave', startAutoSlide);

updateSlides();
startAutoSlide();
