document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear previous content and select options
      activitiesList.innerHTML = "";
      activitySelect.innerHTML = '<option value="">-- Select an activity --</option>';

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft = details.max_participants - details.participants.length;

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
        `;

        // Participants section (use DOM methods to avoid HTML injection)
        const participantsWrap = document.createElement("div");
        participantsWrap.className = "participants";

        const participantsLabel = document.createElement("strong");
        participantsLabel.textContent = "Participants:";
        participantsWrap.appendChild(participantsLabel);

        const ul = document.createElement("ul");
        ul.className = "participants-list";
        (details.participants || []).forEach((email) => {
          const li = document.createElement("li");
          li.className = "participant-item";

          const span = document.createElement("span");
          span.className = "participant-email";
          span.textContent = email;

          const btn = document.createElement("button");
          btn.className = "participant-remove";
          btn.setAttribute("aria-label", `Remove ${email}`);
          btn.title = "Remove participant";
          btn.innerHTML = "&times;";

          btn.addEventListener("click", async () => {
            if (!confirm(`Remove ${email} from ${name}?`)) return;
            try {
              const res = await fetch(
                `/activities/${encodeURIComponent(name)}/participants?email=${encodeURIComponent(email)}`,
                { method: "DELETE" }
              );
              const data = await res.json();
              if (res.ok) {
                messageDiv.textContent = data.message;
                messageDiv.className = "message success";
                fetchActivities();
              } else {
                messageDiv.textContent = data.detail || "Failed to remove participant";
                messageDiv.className = "message error";
              }
              messageDiv.classList.remove("hidden");
              setTimeout(() => {
                messageDiv.classList.add("hidden");
              }, 5000);
            } catch (err) {
              messageDiv.textContent = "Failed to remove participant. Please try again.";
              messageDiv.className = "message error";
              messageDiv.classList.remove("hidden");
              console.error("Error removing participant:", err);
            }
          });

          li.appendChild(span);
          li.appendChild(btn);
          ul.appendChild(li);
        });
        participantsWrap.appendChild(ul);

        activityCard.appendChild(participantsWrap);

        activitiesList.appendChild(activityCard);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });
    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "message success";
        signupForm.reset();
        // Refresh activities so participants list and availability update
        fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "message error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  // Initialize app
  fetchActivities();
});
