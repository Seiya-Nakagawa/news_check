all:
  children:
    news_check:
      hosts:
        news_check_server:
          ansible_host: ${public_ip}
          ansible_user: ubuntu
          # Private Keyは ~/.ssh/id_rsa 等、Ansible実行環境のデフォルトを使用するか
          # 必要に応じて ansible_ssh_private_key_file を指定してください
