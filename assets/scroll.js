let lastScrollTop = 0;
const header = document.querySelector(".header");

window.addEventListener("scroll", function() {
    let scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    if (scrollTop > lastScrollTop) {
        // Downscroll
        header.style.top = "-100px";
    } else {
        // Upscroll
        header.style.top = "0";
    }
    lastScrollTop = scrollTop;
});
