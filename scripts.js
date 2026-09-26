const myModal = document.getElementById('myModal')

myModal.addEventListener('show.bs.modal', event => {
  const button = event.relatedTarget
  
  const idAtividade = button.getAttribute('data-atividade-id')
  
  const confirmBtn = myModal.querySelector('#delete')
  
  confirmBtn.href = "/excluir_atividade/" + idAtividade
})