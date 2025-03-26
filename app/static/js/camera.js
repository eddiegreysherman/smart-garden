document.addEventListener("DOMContentLoaded", function () {
  // Update last update time
  function updateLastUpdateTime() {
    const now = new Date();
    document.getElementById("last-update-time").textContent =
      now.toLocaleString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: true,
      });
  }

  // Initial update
  updateLastUpdateTime();

  // Refresh button functionality
  document.getElementById("refresh-btn").addEventListener("click", function () {
    const imgElement = document.querySelector(
      'img[alt="Raspberry Pi Camera Stream"]',
    );
    imgElement.src = "{{ url_for('video_feed') }}?" + new Date().getTime();
    updateLastUpdateTime();
  });

  // Snapshot button functionality
  document
    .getElementById("snapshot-btn")
    .addEventListener("click", function () {
      fetch("{{ url_for('capture_snapshot') }}")
        .then((response) => response.json())
        .then((data) => {
          if (data.success) {
            alert("Snapshot saved successfully!");
          } else {
            alert("Failed to capture snapshot.");
          }
        })
        .catch((error) => {
          console.error("Error:", error);
          alert("An error occurred while capturing snapshot.");
        });
    });
});
