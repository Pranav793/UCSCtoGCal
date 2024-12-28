import axios from 'axios'

const api = axios.create({
    baseURL: 'https://ucsctogcal.onrender.com',
})

export default api;