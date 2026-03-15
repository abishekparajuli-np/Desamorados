import React from 'react'

export default function BookingFlow() {
  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold mb-8 text-center">बुकिङ फ्लो</h1>
        <div className="bg-white rounded-lg shadow-md p-8">
          <p className="text-gray-600 text-center mb-6">यो पृष्ठ अभी निर्माणाधीन छ।</p>
          <div className="space-y-6">
            <div className="border-l-4 border-primary-700 pl-4">
              <h3 className="font-bold mb-2">चरण 1: समस्या वर्णन गर्नुहोस्</h3>
              <p className="text-gray-600">पाठ वा फोटो अपलोड गरि आपको समस्या प्रदर्शित गर्नुहोस्</p>
            </div>
            <div className="border-l-4 border-primary-700 pl-4">
              <h3 className="font-bold mb-2">चरण 2: मूल्य अनुमान</h3>
              <p className="text-gray-600">AI द्वारा मूल्य अनुमान देखुन्नुहोस्</p>
            </div>
            <div className="border-l-4 border-primary-700 pl-4">
              <h3 className="font-bold mb-2">चरण 3: तारिख र समय चयन</h3>
              <p className="text-gray-600">आपको सुविधाजनक समय चयन गर्नुहोस्</p>
            </div>
            <div className="border-l-4 border-primary-700 pl-4">
              <h3 className="font-bold mb-2">चरण 4: प्रदान गर्नेहरू मिलाउन</h3>
              <p className="text-gray-600">AI सुझाईसहित शीर्ष प्रदान गर्नेहरू देखुन्नुहोस्</p>
            </div>
            <div className="border-l-4 border-primary-700 pl-4">
              <h3 className="font-bold mb-2">चरण 5: कन्फर्मेशन र भुक्तानी</h3>
              <p className="text-gray-600">बुकिङ कन्फर्म गरि भुक्तानी पूरा गर्नुहोस्</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
