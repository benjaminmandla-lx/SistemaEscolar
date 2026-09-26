window.onload = carregarDashboard;


function carregarDashboard() {

    fetch('/api/dados_dashboard')

        .then(response => response.json())

        .then(dados => {

            // ==========================================
            // CARDS
            // ==========================================

            document.getElementById('cardMedia').innerText =
                dados.media_geral.toFixed(2);

            document.getElementById('cardAtividades').innerText =
                dados.total_atividades;

            document.getElementById('cardMaterias').innerText =
                dados.total_materias;


            // ==========================================
            // TABELA DE ATIVIDADES RECENTES
            // ==========================================

            const tabela =
                document.getElementById('tabelaRecentes');

            tabela.innerHTML = "";


            if (dados.recentes.length === 0) {

                tabela.innerHTML = `
                    <tr>
                        <td
                            colspan="4"
                            class="text-center text-muted"
                        >
                            Nenhuma atividade registrada.
                        </td>
                    </tr>
                `;

            } else {

                dados.recentes.forEach(atividade => {

                    let nota = "-";

                    if (atividade.nota !== null) {

                        nota = atividade.nota.toFixed(2);

                    }


                    tabela.innerHTML += `

                        <tr>

                            <td>
                                ${atividade.data}
                            </td>

                            <td>
                                ${atividade.atividade}
                            </td>

                            <td>
                                ${atividade.materia}
                            </td>

                            <td class="text-center fw-bold">
                                ${nota}
                            </td>

                        </tr>

                    `;

                });

            }


            // ==========================================
            // GRÁFICO DE NOTAS
            // ==========================================

            const canvasNotas =
                document.getElementById('graficoNotas');

            new Chart(canvasNotas, {

                type: 'line',

                data: {

                    labels: dados.notas_por_data.map(
                        item =>
                            formatarData(item.data)
                    ),

                    datasets: [{

                        label: 'Nota',

                        data: dados.notas_por_data.map(
                            item => item.nota
                        ),

                        borderWidth: 2,

                        tension: 0.3,

                        fill: false

                    }]

                },

                options: {

                    responsive: true,

                    maintainAspectRatio: false,

                    scales: {

                        y: {

                            beginAtZero: true,

                            max: 10,

                            title: {

                                display: true,

                                text: 'Nota'

                            }

                        }

                    }

                }

            });


            // ==========================================
            // GRÁFICO DE MATÉRIAS
            // ==========================================

            const canvasMaterias =
                document.getElementById('graficoMaterias');


            new Chart(canvasMaterias, {

                type: 'doughnut',

                data: {

                    labels:
                        Object.keys(
                            dados.atividades_por_materia
                        ),

                    datasets: [{

                        data:
                            Object.values(
                                dados.atividades_por_materia
                            ),

                        borderWidth: 1

                    }]

                },

                options: {

                    responsive: true,

                    maintainAspectRatio: false,

                    plugins: {

                        legend: {

                            position: 'bottom'

                        }

                    }

                }

            });

        })

        .catch(error => {

            console.error(
                "Erro ao carregar o Dashboard:",
                error
            );

        });

}


// ==========================================
// FORMATAR DATA
// ==========================================

function formatarData(data) {

    if (!data) {
        return "-";
    }

    const dataObjeto = new Date(data);

    return dataObjeto.toLocaleDateString(
        'pt-BR',
        {
            timeZone: 'UTC'
        }
    );
}