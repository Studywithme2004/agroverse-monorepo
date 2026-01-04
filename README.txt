AgroVerse v6 — Frontend-only Smart Farm
Files:
- index.html, login.html, signup.html
- farmer-dashboard.html, admin-dashboard.html, crop-report.html
- style.css, script.js, ai.js
- data/crops.json (25 crops with image URLs)
- assets/leaf-back.png (user-provided background)
How to use:
1. Unzip and open index.html in your browser, or serve the folder with: python -m http.server 8000
2. Login as farmer@example.com / 12345 or admin@example.com / admin123
3. Explore crops, view reports, use AI assistant (offline)
Notes:
- All data stored in localStorage. Admin can add/delete crops.
- Real images are hotlinked from Unsplash (internet required to load images).
