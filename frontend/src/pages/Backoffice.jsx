// frontend/src/pages/Backoffice.jsx
export default function Backoffice({ me }) {
  return (
    <div className="container">
      <h2>Backoffice</h2>
      <p>Hola {me?.username}. Acá vas a gestionar publicaciones.</p>
    </div>
  );
}
