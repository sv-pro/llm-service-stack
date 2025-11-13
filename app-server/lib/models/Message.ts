import mongoose, { Document, Schema, Types } from 'mongoose';

export interface IMessage extends Document {
  sessionId: Types.ObjectId;
  role: 'user' | 'assistant' | 'system';
  content: string;
  tokens?: number;
  cost?: number;
  createdAt: Date;
}

const MessageSchema = new Schema<IMessage>(
  {
    sessionId: {
      type: Schema.Types.ObjectId,
      ref: 'Session',
      required: true,
      index: true,
    },
    role: {
      type: String,
      required: true,
      enum: ['user', 'assistant', 'system'],
    },
    content: {
      type: String,
      required: true,
    },
    tokens: {
      type: Number,
    },
    cost: {
      type: Number,
    },
    createdAt: {
      type: Date,
      default: Date.now,
      index: true,
    },
  },
  {
    timestamps: false, // Use manual createdAt only
  }
);

// Indexes for performance
MessageSchema.index({ sessionId: 1, createdAt: 1 });

export const Message = mongoose.models.Message || mongoose.model<IMessage>('Message', MessageSchema);
