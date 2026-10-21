import React from 'react';
import 'chart.js/auto';
import { Line } from 'react-chartjs-2';

function PriceChart({ priceHistory }) {
  const data = {
    labels: priceHistory.map(item => item.date),
    datasets: priceHistory.map((product, index) => ({
      label: product.name,
      data: product.prices,
      borderColor: `rgba(${index * 50}, 99, 132, 1)`,
      backgroundColor: `rgba(${index * 50}, 99, 132, 0.2)`
    }))
  };

  return <Line data={data} />;
}

export default PriceChart;
