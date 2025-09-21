<?php
// trip.php
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Personalised Trip Planner</title>
    <!-- Google Font -->
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@500;600&display=swap" rel="stylesheet">
    <style>
        html, body {
            margin: 0;
            padding: 0;
            font-family: 'Poppins', sans-serif;
            background: #f0f4f8;
            color: #333;
            height: 100%;
            width: 100%;
        }
        body {
            display: flex;
            flex-direction: column;
        }
        header {
            background: #1e3a8a;
            color: white;
            text-align: center;
            padding: 40px 0;
            font-size: 48px;
            font-weight: 600;
            letter-spacing: 1px;
        }
        main {
            flex: 1;
            display: flex;
            justify-content: center;
            align-items: center;
            overflow: hidden;
        }
        main img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        footer {
            width: 100%;
            background: #1e3a8a;
            color: #fff;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px;
            box-sizing: border-box;
        }
        footer .credit {
            font-size: 14px;
            margin-bottom: 10px;
            text-align: center;
        }
        footer a {
            background: #facc15;
            color: #111;
            padding: 14px 24px;
            text-decoration: none;
            font-weight: bold;
            border-radius: 6px;
            box-shadow: 0px 4px 6px rgba(0,0,0,0.3);
            transition: background 0.3s ease;
        }
        footer a:hover {
            background: #fbbf24;
        }
    </style>
</head>
<body>
    <header>
        Personalised Trip Planner
    </header>
    <main>
        <img src="img/easemytrip.png" alt="Trip Image">
    </main>
    <footer>
        <a href="#">Book Your Trip</a>
        <br>
        <div class="credit">
            Designed and developed by <strong>Team GSDL</strong> 
            (Souvik Sankar Mitra and Devendra Nagpure) for 
            <strong>Google GenAI Exchange Hackathon</strong>
        </div>
        
    </footer>

    <script type="module">
  // Import the functions you need from the SDKs you need
  import { initializeApp } from "https://www.gstatic.com/firebasejs/12.2.1/firebase-app.js";
  import { getAnalytics } from "https://www.gstatic.com/firebasejs/12.2.1/firebase-analytics.js";
  // TODO: Add SDKs for Firebase products that you want to use
  // https://firebase.google.com/docs/web/setup#available-libraries

  // Your web app's Firebase configuration
  // For Firebase JS SDK v7.20.0 and later, measurementId is optional
  const firebaseConfig = {
    apiKey: "AIzaSyA3Is_0asWmNhGVN72fSzTwWS7mmdAOKAs",
    authDomain: "trip-planner-genai-hackathon.firebaseapp.com",
    projectId: "trip-planner-genai-hackathon",
    storageBucket: "trip-planner-genai-hackathon.firebasestorage.app",
    messagingSenderId: "1071638693675",
    appId: "1:1071638693675:web:bb6045a93e5c3ac4e5676e",
    measurementId: "G-5C8ZLEJDG7"
  };

  // Initialize Firebase
  const app = initializeApp(firebaseConfig);
  const analytics = getAnalytics(app);
</script>
</body>
</html>
