 
 function togglePass() {
      const inp  = document.getElementById('pass');
      const icon = document.getElementById('eye');
      if (inp.type === 'password') {
        inp.type = 'text';
        icon.innerHTML = `
          <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/>
          <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/>
          <line x1="1" y1="1" x2="23" y2="23"/>`;
      } else {
        inp.type = 'password';
        icon.innerHTML = `
          <path d="M1 12S5 4 12 4s11 8 11 8-4 8-11 8S1 12 1 12z"/>
          <circle cx="12" cy="12" r="3"/>`;
      }
    }