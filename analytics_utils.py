import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import os
import io
import base64
import warnings
from fpdf import FPDF
import tempfile

warnings.filterwarnings('ignore')

# Configuración estética profesional
sns.set_theme(style="whitegrid")
plt.style.use('seaborn-v0_8-muted')

class ScientificAudit:
    def __init__(self, df, dataset_name="Dataset", metadata=None):
        self.df = df
        if not isinstance(self.df.index, pd.DatetimeIndex):
            self.df.index = pd.to_datetime(self.df.index)
        
        self.dataset_name = dataset_name
        self.metadata = metadata or {}
        self.df_numerico = df.select_dtypes(include=[np.number])
        self.author = "Raul Alejandro Morales Rivera, DCI, Posgrado FIT"
        
    def _fig_to_base64(self, fig):
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=140, bbox_inches='tight')
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        return img_str

    def generate_html_report(self):
        """Genera el reporte HTML optimizado con ancho completo y metadata corregida."""
        n_filas, n_cols = self.df.shape
        porc_nulos = (self.df.isnull().sum().sum() / (n_filas * n_cols)) * 100
        
        # 1. Resumen Estadístico
        stats_html = self.df_numerico.describe(percentiles=[.01, .25, .5, .75, .99]).round(4).to_html(classes='scientific-table')

        # 2. SECCIÓN TEMPORAL (Solo Boxplots con años verticales)
        temporal_html = ""
        if not self.df_numerico.empty:
            yearly_stats = self.df_numerico.groupby(self.df.index.year).agg(['count', 'mean', 'std', 'min', 'max']).round(4)
            temporal_html += "<h3>2. Auditoría Anual Detallada</h3>"
            temporal_html += f'<div style="overflow-x: auto; margin-bottom: 30px;">{yearly_stats.to_html(classes="scientific-table")}</div>'
            
            for col in self.df_numerico.columns:
                meta = self.metadata.get(col, {})
                full_name = f"{meta.get('long_name', col)} ({col})"
                
                fig_b, ax_b = plt.subplots(figsize=(14, 6))
                df_box = self.df[[col]].copy()
                df_box['Año'] = df_box.index.year
                sns.boxplot(data=df_box, x='Año', y=col, color="#818cf8", ax=ax_b)
                ax_b.set_title(f"Distribución Anual: {full_name}")
                plt.xticks(rotation=90) # Años verticales
                temporal_html += f'<div class="chart-container-full"><img src="data:image/png;base64,{self._fig_to_base64(fig_b)}"></div>'

        # 3. Fichas Técnicas (Ancho completo)
        dist_visuals = "<h3>3. Fichas Técnicas y Distribución de Variables</h3>"
        for col in self.df_numerico.columns:
            meta = self.metadata.get(col, {})
            full_name = f"{meta.get('long_name', col)} ({col})"
            units = meta.get('units', 'N/A')
            v_min, v_max = meta.get('min', self.df[col].min()), meta.get('max', self.df[col].max())

            dist_visuals += f"""
            <div class="variable-sheet-full">
                <h4>{full_name}</h4>
                <div class="meta-grid">
                    <p><strong>Unidades:</strong> {units}</p>
                    <p><strong>Rango Global:</strong> {v_min:.4f} a {v_max:.4f} {units}</p>
                </div>
            </div>
            """
            # Gráficos de ancho completo centrados
            fig_v, ax_v = plt.subplots(figsize=(14, 5))
            sns.violinplot(x=self.df[col], color="#818cf8", inner="quart", ax=ax_v)
            ax_v.set_title(f"Densidad de Probabilidad (Violín): {full_name}")
            dist_visuals += f'<div class="chart-container-full"><img src="data:image/png;base64,{self._fig_to_base64(fig_v)}"></div>'

            fig_h, ax_h = plt.subplots(figsize=(14, 5))
            sns.histplot(self.df[col], kde=True, color="#38bdf8", ax=ax_h)
            ax_h.set_title(f"Frecuencia de Ocurrencia (Histograma): {full_name}")
            dist_visuals += f'<div class="chart-container-full"><img src="data:image/png;base64,{self._fig_to_base64(fig_h)}"></div>'

        return f"""
        <div class="scientific-report">
            <style>
                .scientific-report {{ font-family: 'Inter', sans-serif; color: #f1f5f9; padding: 20px; }}
                .author-tag {{ font-size: 0.9rem; color: #94a3b8; font-style: italic; margin-bottom: 30px; border-bottom: 2px solid #334155; padding-bottom: 10px; }}
                .scientific-report h2 {{ color: #38bdf8; font-size: 1.5rem; }}
                .scientific-report h3 {{ color: #7dd3fc; border-left: 5px solid #38bdf8; padding-left: 15px; margin-top: 50px; text-transform: uppercase; }}
                .scientific-table {{ width: 100%; border-collapse: collapse; font-size: 0.7rem; background: #0f172a; }}
                .scientific-table th {{ background: #334155; color: #38bdf8; padding: 10px; border: 1px solid #475569; }}
                .scientific-table td {{ padding: 8px; border: 1px solid #334155; text-align: right; }}
                .chart-container-full {{ background: white; padding: 20px; border-radius: 12px; margin: 20px 0; text-align: center; }}
                .chart-container-full img {{ width: 100%; height: auto; display: block; }}
                .variable-sheet-full {{ background: rgba(56, 189, 248, 0.15); border-left: 6px solid #38bdf8; padding: 20px; margin-top: 40px; }}
                .meta-grid {{ display: flex; gap: 40px; font-size: 0.9rem; color: #cbd5e1; margin-top: 10px; }}
            </style>

            <h2>{self.dataset_name}</h2>
            <div class="author-tag">Autor: {self.author}</div>
            
            <h3>1. Resumen Estadístico Multivariante</h3>
            <div style="overflow-x: auto;">{stats_html}</div>

            {temporal_html}
            {dist_visuals}
        </div>
        """

    def generate_pdf_report(self):
        """Genera el PDF con años verticales, metadata corregida y gráficos de ancho completo."""
        pdf = FPDF(orientation='P', unit='mm', format='A4')
        pdf.add_page()
        
        # --- PORTADA ---
        pdf.set_font("Arial", "B", 18)
        pdf.set_text_color(56, 189, 248)
        pdf.cell(0, 15, "INFORME DE AUDITORÍA CIENTÍFICA", ln=True, align="C")
        pdf.set_font("Arial", "I", 11)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(0, 8, f"Autor: {self.author}", ln=True, align="C")
        pdf.ln(10)

        # --- SECCIÓN 1: ESTADÍSTICAS ---
        pdf.set_font("Arial", "B", 14)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, "1. Resumen Estadístico Multivariante", ln=True)
        pdf.ln(5)
        
        if not self.df_numerico.empty:
            estadisticos = self.df_numerico.describe(percentiles=[.01, .25, .5, .75, .99])
            col_width = 190 / (len(self.df_numerico.columns) + 1)
            pdf.set_font("Arial", "B", 8)
            pdf.cell(col_width, 8, "Metrica", border=1, align="C")
            for col in self.df_numerico.columns:
                pdf.cell(col_width, 8, col, border=1, align="C")
            pdf.ln()
            pdf.set_font("Arial", "", 7)
            for row in estadisticos.index:
                pdf.cell(col_width, 7, str(row), border=1)
                for val in estadisticos.loc[row]:
                    pdf.cell(col_width, 7, f"{val:.4f}", border=1, align="R")
                pdf.ln()

        # --- SECCIÓN 2: TEMPORAL (BOXPLOTS) ---
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "2. Análisis de Distribución Anual (Boxplots)", ln=True)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            for col in self.df_numerico.columns:
                meta = self.metadata.get(col, {})
                full_name = f"{meta.get('long_name', col)} ({col})"
                
                pdf.set_font("Arial", "B", 11)
                pdf.cell(0, 10, f"Variable: {full_name}", ln=True)
                
                fig_b, ax_b = plt.subplots(figsize=(10, 5))
                df_box = self.df[[col]].copy()
                df_box['Año'] = df_box.index.year
                sns.boxplot(data=df_box, x='Año', y=col, color="#818cf8", ax=ax_b)
                plt.xticks(rotation=90)
                b_path = os.path.join(tmpdir, f"box_{col}.png")
                fig_b.savefig(b_path, dpi=120, bbox_inches='tight')
                plt.close(fig_b)
                pdf.image(b_path, x=10, w=190)
                pdf.add_page()

            # --- SECCIÓN 3: FICHAS TÉCNICAS (ANCHO COMPLETO) ---
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, "3. Fichas Técnicas y Distribución Detallada", ln=True)
            
            for col in self.df_numerico.columns:
                meta = self.metadata.get(col, {})
                full_name = f"{meta.get('long_name', col)} ({col})"
                units = meta.get('units', 'N/A')
                v_min, v_max = meta.get('min', self.df[col].min()), meta.get('max', self.df[col].max())

                pdf.set_font("Arial", "B", 12)
                pdf.set_text_color(56, 189, 248)
                pdf.cell(0, 10, full_name, ln=True)
                pdf.set_font("Arial", "", 10)
                pdf.set_text_color(0, 0, 0)
                pdf.multi_cell(0, 7, f"Unidades: {units}\nRango Global: {v_min:.4f} a {v_max:.4f} {units}")
                pdf.ln(5)
                
                # Violín (Ancho completo)
                fig_v, ax_v = plt.subplots(figsize=(10, 4))
                sns.violinplot(x=self.df[col], color="#818cf8", ax=ax_v)
                v_path = os.path.join(tmpdir, f"v_full_{col}.png")
                fig_v.savefig(v_path, dpi=120, bbox_inches='tight')
                plt.close(fig_v)
                pdf.image(v_path, x=10, w=190)
                pdf.ln(5)

                # Histograma (Ancho completo)
                fig_h, ax_h = plt.subplots(figsize=(10, 4))
                sns.histplot(self.df[col], kde=True, color="#38bdf8", ax=ax_h)
                h_path = os.path.join(tmpdir, f"h_full_{col}.png")
                fig_h.savefig(h_path, dpi=120, bbox_inches='tight')
                plt.close(fig_h)
                pdf.image(h_path, x=10, w=190)
                pdf.add_page()

        return pdf.output()
