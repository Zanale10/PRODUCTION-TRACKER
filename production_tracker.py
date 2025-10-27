# ------------------- CHART -------------------
if len(selected_machines) == 1:
    # Single machine → Bar chart
    chart_height = 500
    melted_df = filtered_df.melt(
        id_vars=['PIPE'],
        value_vars=['EXPECTED', 'RECORDED'],
        var_name='Type',
        value_name='Output'
    )
    fig = px.bar(
        melted_df,
        x='PIPE',
        y='Output',
        color='Type',
        barmode='group',
        text='Output',
        title=f"Size-wise Expected vs Recorded Output - Machine {selected_machines[0]}",
        labels={'PIPE': 'Size', 'Output': 'Output'},
        color_discrete_map={'EXPECTED': 'grey', 'RECORDED': 'orange'},
        height=chart_height
    )
    fig.update_traces(texttemplate='%{text:.0f}', textposition='outside')
    fig.update_layout(
        uniformtext_minsize=8,
        uniformtext_mode='hide',
        yaxis_title="Output",
        xaxis_title="Size",
        bargap=0.2,
        plot_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    # Multiple machines → Line chart
    chart_height = 500
    # Aggregate by PIPE for all selected machines
    agg_df = filtered_df.groupby('PIPE')[['EXPECTED','RECORDED']].sum().reset_index()
    fig = px.line(
        agg_df,
        x='PIPE',
        y=['EXPECTED','RECORDED'],
        markers=True,
        labels={'value':'Output','PIPE':'Size','variable':'Type'},
        color_discrete_map={'EXPECTED':'grey','RECORDED':'orange'},
        title="Size-wise Expected vs Recorded Output (All Machines)",
        height=chart_height
    )
    # Add data labels on points
    fig.update_traces(texttemplate='%{y:.0f}', textposition='top center')
    fig.update_layout(yaxis_title="Output", xaxis_title="Size", plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)
