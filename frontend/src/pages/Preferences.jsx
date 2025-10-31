import { useEffect, useState } from "react";
import api from "../api";

export default function Preferences() {
  const [form, setForm] = useState({
    budget_min: "", budget_max: "",
    climates: [], activities: [], continents: [],
    duration_min_days: "", duration_max_days: ""
  });

  useEffect(() => {
    api.get("/api/preferences").then((res) => setForm(prev => ({ ...prev, ...res })));
  }, []);

  const update = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const toggleMulti = (k, val) =>
    update(k, form[k].includes(val) ? form[k].filter(x => x !== val) : [...form[k], val]);

  const save = async () => {
    const payload = { ...form };
    ["budget_min", "budget_max", "duration_min_days", "duration_max_days"].forEach(k => {
      if (payload[k] === "") delete payload[k];
      else payload[k] = Number(payload[k]);
    });
    await api.put("/api/preferences", payload);
    alert("Preferencias guardadas");
  };

  const chip = (k, val) => (
    <button type="button"
      className={`px-2 py-1 rounded border ${form[k].includes(val) ? "bg-gray-200" : ""}`}
      onClick={() => toggleMulti(k, val)}>{val}</button>
  );

  const radioChip = (k, val, label) => (
    <button type="button"
      className={`px-3 py-1 rounded border capitalize ${form[k] === val ? "bg-gray-200 font-semibold" : ""}`}
      onClick={() => update(k, val)}>{label || val}</button>
  );

  return (
    <div className="max-w-2xl mx-auto p-4 space-y-4">
      <h1 className="text-xl font-bold">Preferencias de viaje</h1>

      <div className="space-y-2">
        <div className="font-semibold">Tipo de sugerencias</div>
        <div className="flex gap-2 flex-wrap">
          {radioChip("publication_type", "all", "Ambos")}
          {radioChip("publication_type", "hotel", "Hoteles")}
          {radioChip("publication_type", "actividad", "Actividades")}
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <label>Presupuesto mín. (USD)
          <input className="border p-2 w-full" value={form.budget_min}
            onChange={e => update("budget_min", e.target.value)} />
        </label>
        <label>Presupuesto máx. (USD)
          <input className="border p-2 w-full" value={form.budget_max}
            onChange={e => update("budget_max", e.target.value)} />
        </label>

        <label>Duración mín. (días)
          <input className="border p-2 w-full" value={form.duration_min_days}
            onChange={e => update("duration_min_days", e.target.value)} />
        </label>
        <label>Duración máx. (días)
          <input className="border p-2 w-full" value={form.duration_max_days}
            onChange={e => update("duration_max_days", e.target.value)} />
        </label>
      </div>

      <div className="space-y-2">
        <div className="font-semibold">Climas</div>
        <div className="flex gap-2 flex-wrap">
          {["templado", "frio", "tropical", "seco"].map(v => chip("climates", v))}
        </div>
      </div>

      <div className="space-y-2">
        <div className="font-semibold">Actividades</div>
        <div className="flex gap-2 flex-wrap">
          {["playa", "montaña", "ciudad", "gastronomía", "historia", "noche"].map(v => chip("activities", v))}
        </div>
      </div>

      <div className="space-y-2">
        <div className="font-semibold">Continentes</div>
        <div className="flex gap-2 flex-wrap">
          {["américa", "europa", "asia", "áfrica", "oceanía"].map(v => chip("continents", v))}
        </div>
      </div>

      <button className="px-4 py-2 rounded bg-black text-white" onClick={save}>
        Guardar preferencias
      </button>
    </div>
  );
}
