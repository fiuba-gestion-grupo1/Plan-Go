import React, { useState, useEffect, useRef } from "react";
import { useOnClickOutside } from "../../hooks/useOnClickOutside";
import "../../styles/buttons.css";

export default function MultiCategoryDropdown({ 
  allCats = [], 
  selected = [], 
  onApply, 
  onReload 
}) {
  const [open, setOpen] = useState(false);
  const [temp, setTemp] = useState(selected);
  const boxRef = useRef(null);

  useEffect(() => { 
    if (open) setTemp(selected); 
  }, [open, selected]);
  
  useOnClickOutside(boxRef, () => setOpen(false));

  function toggle(c) {
    setTemp(prev => prev.includes(c) ? prev.filter(x => x !== c) : [...prev, c]);
  }
  
  function clear() { 
    setTemp([]); 
  }
  
  function apply() { 
    onApply(temp); 
    setOpen(false); 
  }

  return (
    <div className="position-relative">
      <button
        type="button"
        className="btn btn-outline-custom dropdown-toggle"
        onClick={() => { 
          setOpen(o => !o); 
          if (!open && onReload) onReload(); 
        }}
      >
        Categorías
      </button>
      
      {open && (
        <div
          ref={boxRef}
          className="position-absolute end-0 mt-2 p-3 bg-white border rounded-3 shadow"
          style={{ minWidth: 280, zIndex: 1000, maxHeight: 360, overflow: "auto" }}
        >
          <div className="d-flex align-items-center justify-content-between mb-2">
            <div className="fw-semibold text-muted small">Tipo de categoría</div>
            <button 
              className="btn btn-sm btn-link" 
              type="button" 
              onClick={onReload} 
              title="Actualizar lista"
            >
              ↻
            </button>
          </div>
          
          <ul className="list-unstyled mb-3" style={{ columnGap: 24 }}>
            {allCats.length === 0 && (
              <li className="text-muted small">Sin categorías aún.</li>
            )}
            {allCats.map((c) => (
              <li key={c} className="form-check mb-2">
                <input 
                  id={`cat-${c}`} 
                  type="checkbox" 
                  className="form-check-input" 
                  checked={temp.includes(c)} 
                  onChange={() => toggle(c)} 
                />
                <label 
                  className="form-check-label ms-1 text-capitalize" 
                  htmlFor={`cat-${c}`}
                >
                  {c}
                </label>
              </li>
            ))}
          </ul>
          
          <div className="d-flex justify-content-between gap-2">
            <button 
              className="btn btn-outline-secondary" 
              type="button" 
              onClick={clear}
            >
              Limpiar
            </button>
            <button 
              className="btn btn-outline-custom" 
              type="button" 
              onClick={apply}
            >
              Ver resultados
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
