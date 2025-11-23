import React from "react";

function StatCard({ icon, label, value }) {
  return (
    <div className="card border-0 shadow-sm mb-3">
      <div className="card-body text-center">
        <div className={`fs-1 mb-2 text-${color}`}>{icon}</div>
        <h3 className="mb-0">{value}</h3>
        <p className="text-muted mb-0 small">{label}</p>
      </div>
    </div>
  );
}

export default function StatsSidebar({ stats = [] }) {
  if (stats.length === 0) return null;

  return (
    <div className="col-lg-3">
      <div className="position-sticky" style={{ top: 20 }}>
        <h5 className="mb-3">📊 Estadísticas</h5>
        {stats.map((stat, index) => (
          <StatCard 
            key={index}
            icon={stat.icon}
            label={stat.label}
            value={stat.value}
            color={stat.color}
          />
        ))}
      </div>
    </div>
  );
}
