#!/usr/bin/env python
# coding: utf-8

# In[1]:


import gradio as gr
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import locale
import numpy as np

# Set locale for Indian number formatting
locale.setlocale(locale.LC_NUMERIC, 'en_IN')

# --------------------------
# Helper Functions
# --------------------------
def format_indian(number):
    """Format numbers in Indian format (thousands, lakhs, crores)."""
    number = float(number)
    if number < 1_00_000:
        return locale.format_string("%.0f", number, grouping=True)
    elif number < 1_00_00_000:
        return locale.format_string("%.2fL", number / 1_00_000, grouping=True)
    else:
        return locale.format_string("%.2fCr", number / 1_00_00_000, grouping=True)

# --------------------------
# Tax Calculation Functions
# --------------------------
def calculate_new_regime_2024_25(income):
    taxable_income = max(income - 75_000, 0)
    slabs = [
        (300_000, 0),
        (700_000, 0.05),
        (1_000_000, 0.10),
        (1_200_000, 0.15),
        (1_500_000, 0.20),
        (float('inf'), 0.30)
    ]
    return calculate_tax(taxable_income, slabs)

def calculate_new_regime_2025_26(income):
    taxable_income = max(income - 75_000, 0)
    slabs = [
        (400_000, 0),
        (800_000, 0.05),
        (1_200_000, 0.10),
        (1_600_000, 0.15),
        (2_000_000, 0.20),
        (2_400_000, 0.25),
        (float('inf'), 0.30)
    ]
    return calculate_tax(taxable_income, slabs)

def calculate_tax(income, slabs):
    tax = 0
    prev_slab = 0
    breakdown = []
    
    for slab, rate in slabs:
        if income > prev_slab:
            slab_amount = min(income, slab) - prev_slab
            slab_tax = slab_amount * rate
            tax += slab_tax
            breakdown.append({
                "Slab Range": f"₹{format_indian(prev_slab)} - ₹{format_indian(slab)}",
                "Taxable Amount": slab_amount,
                "Rate": f"{rate*100:.0f}%",
                "Tax": slab_tax
            })
            prev_slab = slab
    return tax, pd.DataFrame(breakdown)

# --------------------------
# Visualization Functions
# --------------------------
def create_comparison_chart(old_tax, new_tax, savings):
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=['2024-25 Tax', '2025-26 Tax'],
        y=[old_tax, new_tax],
        marker_color=['#FFB3BA', '#C2EABD'],
        text=[f'₹{format_indian(y)}' for y in [old_tax, new_tax]],
        textposition='auto'
    ))
    fig.add_trace(go.Bar(
        x=['Savings'],
        y=[savings],
        marker_color='#FFDFBA',
        text=[f'₹{format_indian(savings)}'],
        textposition='auto'
    ))
    fig.update_layout(
        title="Tax Comparison & Savings",
        barmode='group',
        height=400,
        template='plotly_white',
        showlegend=False
    )
    fig.add_annotation(
        text=f"<b>Grand Total Savings: ₹{format_indian(savings)}</b>",
        xref="paper", yref="paper",
        x=0.5, y=-0.15,
        showarrow=False,
        font=dict(size=14, color="black")
    )
    return fig

def create_savings_chart(bracket_savings_df):
    fig = go.Figure()
    
    # Primary axis (Tax amounts)
    fig.add_trace(go.Scatter(
        x=bracket_savings_df['Income Bracket'],
        y=bracket_savings_df['2024-25 Tax'],
        name='2024-25 Tax',
        line=dict(color='#1f77b4')
    ))
    
    fig.add_trace(go.Scatter(
        x=bracket_savings_df['Income Bracket'],
        y=bracket_savings_df['2025-26 Tax'],
        name='2025-26 Tax',
        line=dict(color='#ff7f0e')
    ))

    # Secondary axis (Savings)
    fig.add_trace(go.Scatter(
        x=bracket_savings_df['Income Bracket'],
        y=bracket_savings_df['Savings'],
        name='Savings',
        line=dict(color='#2ca02c'),
        yaxis='y2'
    ))

    fig.update_layout(
        title="Tax Trend Analysis",
        height=400,
        template='plotly_white',
        yaxis=dict(
            title='Tax Amount (₹)',
            titlefont=dict(color='#1f77b4'),
            tickfont=dict(color='#1f77b4')
        ),
        yaxis2=dict(
            title='Savings (₹)',
            titlefont=dict(color='#2ca02c'),
            tickfont=dict(color='#2ca02c'),
            overlaying='y',
            side='right'
        )
    )
    return fig

# --------------------------
# Gradio Interface
# --------------------------
def tax_calculator(income):
    if income is None or income < 0:
        return ("❌ Error: Invalid income input!", *[gr.update()]*8)
    
    old_tax, old_df = calculate_new_regime_2024_25(income)
    new_tax, new_df = calculate_new_regime_2025_26(income)
    savings = old_tax - new_tax

    # Recommendation bar
    recommendation_bar = f"""
    <div style="background-color: #E0F7FA; padding: 10px; border-radius: 5px; text-align: center;">
        <b>💡 Recommendation:</b> {"Switch to 2025-26 Regime" if savings > 0 else "Stick to 2024-25 Regime"} | 
        <b>Total Savings:</b> ₹{format_indian(savings)} ({savings/old_tax*100:.1f}%)
    </div>
    """

    # Final comparison
    final_comparison = f"""
    <div style="background-color: #F5F5F5; padding: 10px; border-radius: 5px;">
        <h3>📊 Final Comparison</h3>
        <ul>
            <li><b>New Regime (2024-25) Tax:</b> ₹{format_indian(old_tax)}</li>
            <li><b>New Regime (2025-26) Tax:</b> ₹{format_indian(new_tax)}</li>
            <li><b>Total Savings:</b> ₹{format_indian(savings)} ({savings/old_tax*100:.1f}% reduction)</li>
        </ul>
    </div>
    """

    # Create visualizations
    comparison_chart = create_comparison_chart(old_tax, new_tax, savings)
    
    # Calculate savings for every 1 lakh bracket
    income_brackets = range(0, int(income) + 100_000, 100_000)
    bracket_savings = []
    for bracket in income_brackets:
        old_tax_bracket, _ = calculate_new_regime_2024_25(bracket)
        new_tax_bracket, _ = calculate_new_regime_2025_26(bracket)
        bracket_savings.append({
            "Income Bracket": f"₹{format_indian(bracket)} - ₹{format_indian(bracket + 100_000)}",
            "2024-25 Tax": old_tax_bracket,
            "2025-26 Tax": new_tax_bracket,
            "Savings": old_tax_bracket - new_tax_bracket
        })
    bracket_savings_df = pd.DataFrame(bracket_savings).replace(np.nan, '-')

    # Add grand totals to main tables
    old_df.loc['Grand Total'] = old_df.sum(numeric_only=True)
    new_df.loc['Grand Total'] = new_df.sum(numeric_only=True)

    # Create savings chart
    savings_chart = create_savings_chart(bracket_savings_df)

    # Format tables
    table_style = [{
        'selector': 'caption',
        'props': [('font-size', '16px'), ('font-weight', 'bold')]
    }]

    old_table = old_df.style         .set_caption("2024-25 Tax Breakdown")         .format({"Taxable Amount": "{:,.0f}", "Tax": "₹{:,.0f}"})         .set_table_styles(table_style)         .set_properties(**{'background-color': '#F0F8FF', 'color': 'black'})

    new_table = new_df.style         .set_caption("2025-26 Tax Breakdown")         .format({"Taxable Amount": "{:,.0f}", "Tax": "₹{:,.0f}"})         .set_table_styles(table_style)         .set_properties(**{'background-color': '#FAFAD2', 'color': 'black'})

    savings_table = bracket_savings_df.style         .set_caption("Savings per 1 Lakh Bracket")         .format({"2024-25 Tax": "₹{:,.0f}", "2025-26 Tax": "₹{:,.0f}", "Savings": "₹{:,.0f}"})         .background_gradient(subset=['Savings'], cmap='YlGnBu_r')         .set_table_styles(table_style)         .set_properties(**{'background-color': '#FFFACD', 'color': 'black'})

    return (
        recommendation_bar,
        final_comparison,
        old_table._repr_html_(),
        new_table._repr_html_(),
        comparison_chart,
        savings_table._repr_html_(),
        savings_chart
    )

# --------------------------
# Gradio Layout
# --------------------------
with gr.Blocks(title="💰 Tax Regime Comparator 2024-25 vs 2025-26", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 💰 Tax Regime Comparator 
    ### Compare 2024-25 vs 2025-26 New Tax Regimes
    """)

    with gr.Row():
        with gr.Column(scale=2):
            income_input = gr.Number(
                label="Annual Taxable Income (₹)",
                minimum=0,
                maximum=10_000_000,
                value=1_500_000,
                step=50_000,
                elem_id="income_input"
            )
            income_slider = gr.Slider(
                label="Set Income",
                minimum=0,
                maximum=10_000_000,
                value=1_500_000,
                step=50_000
            )
            gr.Markdown("### Sample Income Values")
            with gr.Row():
                for value in [500_000, 1_000_000, 1_500_000, 2_000_000, 2_500_000, 3_000_000]:
                    gr.Button(
                        f"₹{format_indian(value)}",
                        variant="secondary"
                    ).click(
                        lambda v=value: v,
                        inputs=None,
                        outputs=income_input
                    )
        with gr.Column(scale=1):
            gr.Markdown("### Actions")
            with gr.Row():
                calculate_btn = gr.Button("Calculate", variant="primary")
                reset_btn = gr.Button("Reset")

    with gr.Row():
        recommendation_bar = gr.HTML()
    with gr.Row():
        final_comparison = gr.HTML()

    with gr.Row():
        with gr.Column():
            gr.Markdown("### 2024-25 Regime Breakdown")
            old_table = gr.HTML()
        with gr.Column():
            gr.Markdown("### 2025-26 Regime Breakdown")
            new_table = gr.HTML()

    with gr.Row():
        with gr.Column():
            gr.Markdown("### Tax Comparison")
            comparison_chart = gr.Plot()
        with gr.Column():
            gr.Markdown("### Tax Trend Analysis")
            savings_chart = gr.Plot()

    with gr.Row():
        with gr.Column():
            gr.Markdown("### Savings per 1 Lakh Bracket")
            savings_table = gr.HTML()

    # Event handlers
    calculate_btn.click(
        tax_calculator,
        inputs=income_input,
        outputs=[recommendation_bar, final_comparison, old_table, new_table, 
                comparison_chart, savings_table, savings_chart]
    )

    reset_btn.click(
        lambda: ["", "", "", "", gr.update(visible=False), "", gr.update(visible=False)],
        outputs=[recommendation_bar, final_comparison, old_table, new_table, 
                comparison_chart, savings_table, savings_chart]
    )

    income_slider.change(
        lambda x: x,
        inputs=income_slider,
        outputs=income_input
    )

demo.launch(inbrowser=True)


# In[ ]:




