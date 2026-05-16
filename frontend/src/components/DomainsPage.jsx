import React, { useState, useEffect } from 'react';
import * as api from '../api';

const DOMAIN_META = {
  general: { icon: 'fa-solid fa-globe', color: '#6366f1', bg: 'rgba(99,102,241,.08)' },
  legal: { icon: 'fa-solid fa-scale-balanced', color: '#8b5cf6', bg: 'rgba(139,92,246,.08)' },
  medical: { icon: 'fa-solid fa-heart-pulse', color: '#ef4444', bg: 'rgba(239,68,68,.08)' },
  finance: { icon: 'fa-solid fa-chart-line', color: '#10b981', bg: 'rgba(16,185,129,.08)' },
  education: { icon: 'fa-solid fa-graduation-cap', color: '#f59e0b', bg: 'rgba(245,158,11,.08)' },
  technical: { icon: 'fa-solid fa-code', color: '#06b6d4', bg: 'rgba(6,182,212,.08)' },
  customer_support: { icon: 'fa-solid fa-headset', color: '#ec4899', bg: 'rgba(236,72,153,.08)' },
};

const FALLBACK_DOMAINS = [
  { name: 'general', label: 'General', description: 'General document Q&A' },
  { name: 'legal', label: 'Legal', description: 'Contract and policy focused RAG' },
  { name: 'medical', label: 'Medical', description: 'Clinical and health document RAG' },
  { name: 'finance', label: 'Finance', description: 'Finance document RAG' },
  { name: 'education', label: 'Education', description: 'Learning material RAG' },
  { name: 'technical', label: 'Technical', description: 'Engineering and code document RAG' },
  { name: 'customer_support', label: 'Customer Support', description: 'Support knowledge-base RAG' },
];

export default function DomainsPage() {
  const [domains, setDomains] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getDomains()
      .then((d) => setDomains(d.length > 0 ? d : FALLBACK_DOMAINS))
      .catch(() => setDomains(FALLBACK_DOMAINS))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="empty-state">
        <div className="spinner spinner-lg" />
        <p style={{ marginTop: 14 }}>Loading domains...</p>
      </div>
    );
  }

  return (
    <div>
      <p style={{ color: 'var(--text-secondary)', marginBottom: 24, fontSize: 14, lineHeight: 1.6 }}>
        <i className="fa-solid fa-circle-info" style={{ color: 'var(--primary)', marginRight: 6 }} />
        Each domain configures the RAG pipeline with specialized system prompts and metadata filters for optimal results.
      </p>

      <div className="domain-grid">
        {domains.map((d) => {
          const meta = DOMAIN_META[d.name] || DOMAIN_META.general;
          return (
            <div key={d.name} className="domain-card" id={`domain-${d.name}`}>
              <div className="domain-card-icon" style={{ background: meta.bg, color: meta.color }}>
                <i className={meta.icon} />
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                <h3>{d.label}</h3>
                <span className="badge badge-primary" style={{ fontSize: 11 }}>{d.name}</span>
              </div>
              <p>{d.description}</p>
              <div style={{ marginTop: 16, display: 'flex', gap: 8 }}>
                <span className="badge badge-success"><i className="fa-solid fa-check" style={{ fontSize: 10 }} /> Active</span>
                <span className="badge badge-accent"><i className="fa-solid fa-bolt" style={{ fontSize: 10 }} /> 4 RAG Modes</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
