// script.js

document.addEventListener('DOMContentLoaded', function () {
    var tocItems = document.querySelectorAll('.toc-item > a');

    tocItems.forEach(function (item) {
        item.addEventListener('click', function (e) {
            if (this.classList.contains("has_page")) {
                return
            }

            e.preventDefault(); // Prevent the default link behavior
            

            var subItems = item.nextElementSibling;

            if (subItems && subItems.classList.contains('sub-items')) {
                // Toggle visibility
                if (subItems.style.display === 'none' || subItems.style.display === '') {
                    subItems.style.display = 'block';
                } else {
                    subItems.style.display = 'none';
                }
            }

            // Optionally, scroll to the section
            var targetId = item.getAttribute('href').substring(1);
            var targetElement = document.getElementById(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
});