// Año actual en el pie de página
document.getElementById("year").textContent = new Date().getFullYear();

// Menú para móvil
const toggle = document.querySelector(".nav__toggle");
const links = document.querySelector(".nav__links");

toggle.addEventListener("click", () => {
  const open = links.classList.toggle("open");
  toggle.setAttribute("aria-expanded", open);
});

links.querySelectorAll("a").forEach((a) =>
  a.addEventListener("click", () => {
    links.classList.remove("open");
    toggle.setAttribute("aria-expanded", false);
  })
);

// Animación al hacer scroll
const observer = new IntersectionObserver(
  (entries) =>
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("visible");
        observer.unobserve(entry.target);
      }
    }),
  { threshold: 0.15 }
);

document.querySelectorAll(".section .container > *, .card").forEach((el) => {
  el.classList.add("reveal");
  observer.observe(el);
});

// Formulario de contacto: abre el correo del visitante con el mensaje listo.
// Cambia este correo por el de tu negocio.
const EMAIL_NEGOCIO = "contacto@minegocio.com";

document.getElementById("contact-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const data = new FormData(e.target);
  const subject = `Mensaje de ${data.get("nombre")}`;
  const body = `${data.get("mensaje")}\n\n— ${data.get("nombre")} (${data.get("correo")})`;
  window.location.href = `mailto:${EMAIL_NEGOCIO}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
});
