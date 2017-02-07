eval $(ssh-agent -s)
chmod 600 travis.pem
ssh-add travis.pem
git remote add deploy django@dev.mbell.me:~django/repo/code.git
git push deploy
