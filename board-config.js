// 掲示板の公開の置き場。クランの仲間がスマホから書けるようにする時は、Firebase Realtime Database の URL を入れる。
//   例: window.BOARD_CONFIG = { firebase: 'https://xxxx-default-rtdb.asia-southeast1.firebasedatabase.app' };
// 空のままなら、手元では tools/save_server.py、GitHub Pages では data/board/ の写しを読むだけになる。
window.BOARD_CONFIG = { firebase: 'https://saz-board-default-rtdb.asia-southeast1.firebasedatabase.app' };
