window.onload = loadData;


function loadData() {

    notas_por_atividade();

    atividades_por_materia();

}


// ============================================================
// GRÁFICO DE NOTAS
// ============================================================

function notas_por_atividade() {

    fetch('/api/notas_por_atividade')

        .then(response => response.json())

        .then(dados => {

            const labels = dados.map(item => {

                if (item.data) {

                    return `${setDateFormat(item.data)} - ${item.atividade}`;

                }

                return item.atividade;

            });


            const notas = dados.map(
                item => item.nota
            );


            const ctx = document
                .getElementById('graficoEvolucao')
                .getContext('2d');


            new Chart(ctx, {

                type: 'line',

                data: {

                    labels: labels,

                    datasets: [{

                        label: 'Nota',

                        data: notas,

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

                        },


                        x: {

                            title: {

                                display: true,

                                text: 'Atividade'

                            }

                        }

                    }

                }

            });

        })


        .catch(error => {

            console.error(
                "Erro ao carregar notas:",
                error
            );

        });

}


// ============================================================
// GRÁFICO DE ATIVIDADES POR MATÉRIA
// ============================================================

function atividades_por_materia() {

    fetch('/api/atividades_por_materia')

        .then(response => response.json())

        .then(dados => {

            const ctx = document
                .getElementById('graficoDonut')
                .getContext('2d');


            new Chart(ctx, {

                type: 'doughnut',

                data: {

                    labels: Object.keys(dados),

                    datasets: [{

                        label: 'Quantidade de Atividades',

                        data: Object.values(dados),

                        backgroundColor: [

                            'rgba(40, 167, 69, 0.6)',

                            'rgba(0, 123, 255, 0.6)',

                            'rgba(255, 193, 7, 0.6)',

                            'rgba(255, 0, 0, 0.6)',

                            'rgba(111, 66, 193, 0.6)'

                        ],

                        borderWidth: 1

                    }]

                },


                options: {

                    responsive: true,

                    plugins: {

                        legend: {

                            position: 'bottom'

                        }

                    },

                    layout: {

                        padding: 30

                    }

                }

            });

        })


        .catch(error => {

            console.error(
                "Erro ao carregar atividades por matéria:",
                error
            );

        });

}


// ============================================================
// FORMATA DATA
// ============================================================

function setDateFormat(date) {

    const dateObject = new Date(date);

    return dateObject.toLocaleDateString(
        'pt-BR',
        {
            timeZone: 'UTC'
        }
    );

}
