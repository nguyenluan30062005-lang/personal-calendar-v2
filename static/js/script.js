// Initialize moment with Vietnamese locale
moment.locale('vi');

// Global variables
let currentDate = new Date();
let selectedDate = null;
let events = {};

// DOM Elements
const calendarGrid = document.getElementById('calendarGrid');
const currentMonthElement = document.getElementById('currentMonth');
const eventDateInput = document.getElementById('eventDate');
const viewDateInput = document.getElementById('viewDate');
const eventDescriptionInput = document.getElementById('eventDescription');
const addEventForm = document.getElementById('addEventForm');
const eventsResult = document.getElementById('eventsResult');
const upcomingEventsList = document.getElementById('upcomingEventsList');
const eventModal = document.getElementById('eventModal');
const modalContent = document.getElementById('modalContent');
const closeModal = document.getElementById('closeModal');
const toast = document.getElementById('toast');
const toastMessage = document.getElementById('toastMessage');
const toastIcon = document.getElementById('toastIcon');
const colorOptions = document.querySelectorAll('.color-option');
const eventColorInput = document.getElementById('eventColor');

// Initialize application
function initApp() {
    // Set today's date as default
    const today = new Date().toISOString().split('T')[0];
    eventDateInput.value = today;
    eventDateInput.min = today;
    viewDateInput.value = today;
    
    // Initialize calendar
    renderCalendar(currentDate);
    
    // Load events
    loadEventsFromServer();
    
    // Setup event listeners
    setupEventListeners();
    
    // Select today's date
    selectDate(new Date());
    
    // Load upcoming events
    loadUpcomingEvents();
}

// Render calendar
function renderCalendar(date) {
    const year = date.getFullYear();
    const month = date.getMonth();
    
    // Update month display
    currentMonthElement.textContent = moment(date).format('MMMM, YYYY');
    
    // Calculate first and last day of month
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const startDate = new Date(firstDay);
    startDate.setDate(firstDay.getDate() - firstDay.getDay());
    
    // Clear calendar grid
    calendarGrid.innerHTML = '';
    
    // Create days
    const todayStr
